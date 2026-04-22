"""Streaming service — runs the Deal agent in-process and streams SSE events to the FE.

Instead of calling the serving endpoint over HTTP, this service imports the
DealIntelligenceAgent directly and calls run_stream() for true token-by-token
streaming from the Claude LLM.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from BE.models.database import Conversation, Document
from BE.utils.logger import get_logger

if TYPE_CHECKING:
    from BE.repositories.chat_repository import ChatRepository
    from BE.repositories.conversation_repository import ConversationRepository
    from BE.repositories.document_repository import DocumentRepository
    from BE.repositories.message_repository import MessageRepository
    from BE.repositories.session_repository import SessionRepository

logger = get_logger(__name__)

# --- Set up Agent - Code on sys.path (once) ---
_agent_code_dir = str(Path(__file__).parent.parent.parent / "Agent - Code")
if _agent_code_dir not in sys.path:
    sys.path.insert(0, _agent_code_dir)


def _ensure_agent_env():
    """Ensure env vars are set so the agent's settings module can load.

    In Databricks Apps, OAuth (client_id + client_secret) is the primary auth.
    We must NOT set DATABRICKS_TOKEN when OAuth creds exist, or the SDK
    will complain about multiple auth methods.
    """
    from BE.settings import get_settings
    s = get_settings()
    host = s.DATABRICKS_HOST or s.databricks_host
    os.environ.setdefault("DATABRICKS_HOST", host)

    # Only set DATABRICKS_TOKEN if OAuth creds are NOT present
    has_oauth = os.environ.get("DATABRICKS_CLIENT_ID") and os.environ.get("DATABRICKS_CLIENT_SECRET")
    if not has_oauth and not os.environ.get("DATABRICKS_TOKEN"):
        token = s.DATABRICKS_TOKEN or s.databricks_token
        if not token:
            try:
                from BE.client.databricks_client import _get_auth_token
                token = _get_auth_token()
            except Exception:
                token = ""
        if token:
            os.environ["DATABRICKS_TOKEN"] = token

    os.environ.setdefault("LLM_ENDPOINT_SONNET", s.llm_endpoint_sonnet)
    os.environ.setdefault("VECTOR_SEARCH_ENDPOINT", s.vector_search_endpoint)
    os.environ.setdefault("VECTOR_SEARCH_INDEX", s.vector_search_index)
    os.environ.setdefault("EMBEDDING_ENDPOINT", s.embedding_endpoint)
    os.environ.setdefault("DATABRICKS_CATALOG", s.DATABRICKS_CATALOG or s.databricks_catalog)
    os.environ.setdefault("DATABRICKS_SCHEMA", s.DATABRICKS_SCHEMA or s.databricks_schema)
    os.environ.setdefault("DATABRICKS_HTTP_PATH", s.DATABRICKS_SQL_HTTP_PATH or "")


class StreamService:
    """Streams Deal agent responses as SSE events by running the agent in-process."""

    def __init__(
        self,
        chat_repository: ChatRepository,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
        conversation_repository: ConversationRepository,
        document_repository: DocumentRepository | None = None,
    ) -> None:
        self._chat_repo = chat_repository
        self._session_repo = session_repository
        self._message_repo = message_repository
        self._conversation_repo = conversation_repository
        self._document_repo = document_repository

    def _enrich_citations(self, agent_result: dict) -> dict:
        """Replace document IDs with human-readable file names."""
        import re
        raw_citations = agent_result.get("citations") or []
        if not raw_citations or not self._document_repo:
            return agent_result

        doc_name_cache: dict[str, str] = {}
        for cit in raw_citations:
            doc_id = cit.get("document_id") if isinstance(cit, dict) else None
            if doc_id and doc_id not in doc_name_cache:
                try:
                    doc = self._document_repo.session.query(Document).filter(
                        Document.document_id == doc_id, Document.is_active == True,
                    ).first()
                    doc_name_cache[doc_id] = doc.file_name if doc else doc_id
                except Exception:
                    doc_name_cache[doc_id] = doc_id

        enriched = []
        for cit in raw_citations:
            if isinstance(cit, dict):
                doc_id = cit.get("document_id")
                doc_name = doc_name_cache.get(doc_id, doc_id) if doc_id else None
                page = cit.get("page_number")
                label = f"{doc_name}, p.{page}" if doc_name and page else cit.get("label")
                enriched.append({**cit, "document_name": doc_name, "short_name": doc_name, "label": label})
            else:
                enriched.append(cit)

        content = agent_result.get("content", "")
        if content:
            content = re.sub(
                r'\[([a-f0-9\-]{36}),\s*p\.(\d+(?:\.\d+)?)\]',
                lambda m: f"[{doc_name_cache.get(m.group(1), m.group(1))}, p.{m.group(2)}]",
                content,
            )

        return {**agent_result, "citations": enriched, "content": content}

    async def stream_deal_response(
        self,
        chat_id: str,
        content: str,
        analyst_type: str,
        scenario_type: str,
        session_id: str | None = None,
        session_title: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Validate inputs, run the agent in-process, and stream back."""
        # --- Validate chat ---
        chat = self._chat_repo.get_chat(chat_id)
        if chat is None:
            yield {"type": "error", "content": f"Chat not found: {chat_id}"}
            return

        # --- Create or validate session ---
        if session_id is None:
            session = self._session_repo.create_session(
                chat_id=chat_id, session_title=session_title, agent_type="deal",
            )
            session_id = session.session_id
        else:
            session = self._session_repo.get_session(session_id)
            if session is None or session.chat_id != chat_id:
                yield {"type": "error", "content": f"Session not found: {session_id}"}
                return

        # --- Save user message ---
        self._message_repo.insert_message(
            session_id=session_id, role="user", content=content, scenario_type=scenario_type,
        )

        # --- Create conversation record ---
        conversation = Conversation(session_id=session_id, user_message=content, response_status="in_progress")
        self._conversation_repo.insert_conversation(conversation)
        conversation_id = str(conversation.conversation_id)

        yield {"type": "session_info", "conversation_id": conversation_id, "session_id": str(session_id)}

        # --- Run the agent in-process with streaming ---
        try:
            _ensure_agent_env()
            from agents.deal_agent import DealIntelligenceAgent

            agent = DealIntelligenceAgent()
            accumulated_content = ""
            metadata = None

            try:
                async for event in agent.run_stream(
                    user_query=content,
                    chat_id=chat_id,
                    analyst_type=analyst_type,
                    scenario_type=scenario_type,
                    session_id=str(session_id),
                ):
                    etype = event.get("type")
                    if etype == "delta":
                        accumulated_content += event.get("content", "")
                    elif etype == "done":
                        metadata = event.get("metadata", {})
                        continue  # Don't yield raw done — wait for enriched version
                    yield event
                    await asyncio.sleep(0)  # flush each event
            except Exception as agent_exc:
                logger.error("Agent run_stream error: %s", str(agent_exc), exc_info=True)
                yield {"type": "error", "content": f"Agent error: {str(agent_exc)[:300]}"}
                return

            # --- Enrich citations and persist ---
            if metadata:
                metadata = self._enrich_citations(metadata)
                # Re-yield the enriched done event
                yield {"type": "done_enriched", "metadata": metadata}

                conversation_obj = self._conversation_repo.get_conversation(conversation_id)
                if conversation_obj:
                    conversation_obj.agent_response = json.dumps(metadata, default=str)
                    conversation_obj.response_status = "completed"
                    conversation_obj.updated_at = datetime.utcnow()
                    self._conversation_repo.session.commit()

                import threading
                persist_data = {"session_id": str(session_id), "content": metadata.get("content", accumulated_content), "metadata": metadata}

                def _persist(data):
                    try:
                        from BE.services.dependencies import _get_session_factory
                        from BE.repositories.message_repository import MessageRepository as MR
                        bg = _get_session_factory()()
                        MR(bg).insert_message(
                            session_id=data["session_id"], role="assistant", content=data["content"],
                            confidence_level=data["metadata"].get("confidence_level"),
                            suggested_questions=data["metadata"].get("suggested_questions"),
                        )
                        bg.commit(); bg.close()
                    except Exception as exc:
                        logger.warning("Background persist failed: %s", str(exc))

                threading.Thread(target=_persist, args=(persist_data,), daemon=True).start()

        except Exception as exc:
            logger.error("Stream service error: %s", str(exc), exc_info=True)
            try:
                conversation_obj = self._conversation_repo.get_conversation(conversation_id)
                if conversation_obj:
                    conversation_obj.response_status = "failed"
                    conversation_obj.updated_at = datetime.utcnow()
                    self._conversation_repo.session.commit()
            except Exception:
                pass
            yield {"type": "error", "content": str(exc)[:500]}
