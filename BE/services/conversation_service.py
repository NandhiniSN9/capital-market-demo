"""Service layer for async conversation CRUD operations.
 
Handles the CRUD side of POST /messages: validates chat/session, saves the
user message, creates a conversation record (in_progress), and returns
immediately. The actual agent processing lives in a separate service/repo.
"""
 
from __future__ import annotations
 
from datetime import datetime
from typing import TYPE_CHECKING
 
from BE.models.database import Conversation
from BE.models.responses import ConversationPollResponse, ConversationResponse
from BE.utils.exceptions import ChatNotFoundException, SessionNotFoundException
from BE.utils.logger import get_logger
 
if TYPE_CHECKING:
    from BE.models.requests import SendMessageRequest
    from BE.repositories.chat_repository import ChatRepository
    from BE.repositories.citation_repository import CitationRepository
    from BE.repositories.conversation_repository import ConversationRepository
    from BE.repositories.document_repository import DocumentRepository
    from BE.repositories.message_repository import MessageRepository
    from BE.repositories.session_repository import SessionRepository
 
logger = get_logger(__name__)
 
 
class ConversationService:
    """CRUD orchestration for conversations — no agent logic."""
 
    def __init__(
        self,
        chat_repository: ChatRepository,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
        conversation_repository: ConversationRepository,
        document_repository: DocumentRepository | None = None,
        citation_repository: CitationRepository | None = None,
    ) -> None:
        self._chat_repo = chat_repository
        self._session_repo = session_repository
        self._message_repo = message_repository
        self._conversation_repo = conversation_repository
        self._document_repo = document_repository
        self._citation_repo = citation_repository
 
    def create_conversation(
        self,
        chat_id: str,
        request: SendMessageRequest,
    ) -> ConversationResponse:
        """Validate inputs, save user message, create conversation record.
 
        Args:
            chat_id: The UUID of the chat workspace.
            request: The SendMessageRequest payload.
 
        Returns:
            ConversationResponse with conversation_id, session_id, status=in_progress.
 
        Raises:
            ChatNotFoundException: If the chat does not exist or is inactive.
            SessionNotFoundException: If session_id is invalid or doesn't belong to chat.
        """
        # Validate chat
        chat = self._chat_repo.get_chat(chat_id)
        if chat is None:
            raise ChatNotFoundException(f"Chat not found: {chat_id}")
 
        # Create or validate session
        if request.session_id is None:
            session = self._session_repo.create_session(
                chat_id=chat_id,
                session_title=request.session_title,
                agent_type=request.agent_type.value if request.agent_type else None,
            )
            session_id = session.session_id
        else:
            session_id_str = str(request.session_id)
            session = self._session_repo.get_session(session_id_str)
            if session is None or session.chat_id != chat_id:
                raise SessionNotFoundException(
                    f"Session not found or does not belong to chat: {session_id_str}"
                )
            session_id = session.session_id
 
        # Save user message
        self._message_repo.insert_message(
            session_id=session_id,
            role="user",
            content=request.content,
            scenario_type=request.scenario_type.value,
        )
 
        # Create conversation record (in_progress)
        conversation = Conversation(
            session_id=session_id,
            user_message=request.content,
            response_status="in_progress",
        )
        self._conversation_repo.insert_conversation(conversation)
 
        now = datetime.utcnow()
        response = ConversationResponse(
            conversation_id=conversation.conversation_id,
            session_id=session_id,
            status="in_progress",
            created_at=now,
        )
 
        # Trigger the agent in a background thread — true fire and forget
        import threading
        from BE.client.databricks_client import DatabricksClient
        from BE.auth.context import get_current_user
 
        payload = {
            "dataframe_records": [{
                "agent_type": "deal",
                "conversation_id": str(conversation.conversation_id),
                "session_id": str(session_id),
                "user_id": get_current_user(),
                "user_message": request.content,
                "persona": "",
                "simulation": "",
                "analyst_type": request.analyst_type.value if request.analyst_type else "",
                "scenario_type": request.scenario_type.value if request.scenario_type else "",
                "chat_id": str(chat_id),
            }]
        }

        logger.info("[AGENT_PAYLOAD] Sending to agent: %s", payload)

        def _trigger():
            try:
                DatabricksClient().trigger(payload)
            except Exception as e:
                logger.warning("Failed to trigger agent: %s", str(e))
 
        threading.Thread(target=_trigger, daemon=True).start()
 
        return response
 
    def get_deal_conversation(self, conversation_id: str) -> "DealConversationResponse":
        """Fetch conversation for the deal endpoint with rich response format.
 
        Parses the agent_response JSON blob and maps all fields to the response model.
        """
        from BE.models.responses import DealConversationResponse
        import json as _json
 
        conversation = self._conversation_repo.get_conversation(conversation_id)
        if conversation is None:
            raise ChatNotFoundException(f"Conversation not found: {conversation_id}")
 
        # Parse the full agent response JSON
        agent_response = conversation.agent_response
        parsed = {}
        if agent_response:
            try:
                if isinstance(agent_response, dict):
                    outer = agent_response
                elif isinstance(agent_response, str):
                    try:
                        outer = _json.loads(agent_response)
                    except Exception:
                        try:
                            import ast
                            outer = ast.literal_eval(agent_response)
                        except Exception:
                            outer = {}
                else:
                    outer = {}
                # Agent stores response nested under 'agent_response' key
                parsed = outer.get("agent_response", outer)
            except Exception:
                parsed = {}
 
        # Enrich citations with document_name from deal_documents table
        raw_citations = parsed.get("citations") or []
        enriched_citations = []
        if raw_citations and self._document_repo:
            import uuid as _uuid
            # Build a cache of document_id -> file_name to avoid repeated DB calls
            doc_name_cache: dict[str, str] = {}
            for cit in raw_citations:
                doc_id = cit.get("document_id") if isinstance(cit, dict) else None
                if doc_id and doc_id not in doc_name_cache:
                    try:
                        # get_documents_by_chat not available here, query directly
                        from BE.models.database import Document
                        doc = self._document_repo.session.query(Document).filter(
                            Document.document_id == doc_id,
                            Document.is_active == True,
                        ).first()
                        doc_name_cache[doc_id] = doc.file_name if doc else doc_id
                    except Exception:
                        doc_name_cache[doc_id] = doc_id
 
            for cit in raw_citations:
                if isinstance(cit, dict):
                    doc_id = cit.get("document_id")
                    doc_name = doc_name_cache.get(doc_id, doc_id) if doc_id else None
                    page = cit.get("page_number")
                    # Generate citation_id if missing
                    cit_id = cit.get("citation_id") or str(_uuid.uuid4())
                    # Build label: "FileName, p.X" — always use resolved doc_name
                    label = (f"{doc_name}, p.{page}" if doc_name and page else None) or cit.get("label")
                    enriched_citations.append({
                        **cit,
                        "citation_id": cit_id,
                        "document_name": doc_name,
                        "short_name": doc_name,
                        "label": label,
                    })
                else:
                    enriched_citations.append(cit)
        else:
            enriched_citations = raw_citations
 
        # Replace [Document UUID, Page X] in content with [FileName, p.X]
        content = parsed.get("content") or ""
        if content and self._document_repo:
            import re
            def replace_doc_ref(match):
                doc_id = match.group(1)
                page = match.group(2)
                name = doc_name_cache.get(doc_id, doc_id) if 'doc_name_cache' in dir() else doc_id
                return f"[{name}, p.{page}]"
            content = re.sub(r'\[Document ([a-f0-9\-]+),\s*Page\s*(\d+)\]', replace_doc_ref, content)
            # Also replace [UUID, p.X] format (e.g. [b5a00930-..., p.13.0])
            def replace_uuid_ref(match):
                doc_id = match.group(1)
                page = match.group(2)
                name = doc_name_cache.get(doc_id, doc_id) if 'doc_name_cache' in dir() else doc_id
                return f"[{name}, p.{page}]"
            content = re.sub(r'\[([a-f0-9\-]{36}),\s*p\.(\d+(?:\.\d+)?)\]', replace_uuid_ref, content)
            # Also replace [Document: UUID, Page X] format
            content = re.sub(r'\[Document:\s*([a-f0-9\-]+),\s*Page\s*(\d+)\]', replace_doc_ref, content)
 
        # Lazy persist in background thread so response returns immediately
        if conversation.response_status == "completed" and parsed.get("content"):
            import threading

            persist_data = {
                "conversation_id": conversation_id,
                "session_id": conversation.session_id,
                "content": content,
                "parsed": parsed,
                "enriched_citations": enriched_citations,
            }

            def _persist_in_background(data):
                try:
                    from BE.services.dependencies import _get_session_factory
                    from BE.repositories.message_repository import MessageRepository
                    from BE.repositories.citation_repository import CitationRepository
                    from BE.models.database import SessionMessage, Citation
                    import json as _json_bg

                    bg_session = _get_session_factory()()
                    bg_message_repo = MessageRepository(bg_session)
                    bg_citation_repo = CitationRepository(bg_session)

                    # Check if already persisted
                    existing = bg_session.query(SessionMessage).filter(
                        SessionMessage.session_id == data["session_id"],
                        SessionMessage.role == "assistant",
                        SessionMessage.content.like(f"%{data['content'][:50]}%") if data["content"] else False,
                        SessionMessage.is_active == True,
                    ).first()

                    if not existing:
                        assistant_msg = bg_message_repo.insert_message(
                            session_id=data["session_id"],
                            role="assistant",
                            content=data["content"],
                            confidence_level=data["parsed"].get("confidence_level"),
                            assumptions=data["parsed"].get("assumptions") if isinstance(data["parsed"].get("assumptions"), str) else (
                                _json_bg.dumps(data["parsed"].get("assumptions")) if data["parsed"].get("assumptions") else None
                            ),
                            calculations=data["parsed"].get("calculations"),
                            suggested_questions=data["parsed"].get("suggested_questions"),
                        )

                        cit_records = []
                        for cit in data["enriched_citations"]:
                            if isinstance(cit, dict) and cit.get("document_id"):
                                cit_records.append(Citation(
                                    citation_id=cit.get("citation_id"),
                                    message_id=assistant_msg.message_id,
                                    document_id=cit["document_id"],
                                    chunk_id=cit.get("chunk_id", ""),
                                    page_number=cit.get("page_number"),
                                    section_name=cit.get("section_name"),
                                    source_text=cit.get("source_text"),
                                ))
                        if cit_records:
                            bg_citation_repo.insert_citations(cit_records)

                        bg_session.commit()
                        logger.info("Background persisted assistant message and %d citations for conversation %s",
                                    len(data["enriched_citations"]), data["conversation_id"])
                except Exception as exc:
                    logger.warning("Background lazy-persist failed: %s", str(exc))
                    try:
                        bg_session.rollback()
                    except Exception:
                        pass
                finally:
                    try:
                        bg_session.close()
                    except Exception:
                        pass

            threading.Thread(target=_persist_in_background, args=(persist_data,), daemon=True).start()
 
        return DealConversationResponse(
            conversation_id=conversation.conversation_id,
            session_id=conversation.session_id,
            status=conversation.response_status,
            user_query=conversation.user_message,
            analyst_type=parsed.get("analyst_type"),
            content=content,
            confidence_level=parsed.get("confidence_level"),
            confidence_reason=parsed.get("confidence_reason"),
            citations=enriched_citations if enriched_citations else None,
            calculations=parsed.get("calculations"),
            source_excerpts=parsed.get("source_excerpts"),
            assumptions=parsed.get("assumptions"),
            suggested_questions=parsed.get("suggested_questions"),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
 
    def get_conversation(self, conversation_id: str) -> ConversationPollResponse:
        """Fetch conversation status for polling."""
        conversation = self._conversation_repo.get_conversation(conversation_id)
        if conversation is None:
            raise ChatNotFoundException(f"Conversation not found: {conversation_id}")
 
        import json as _json
        agent_response = conversation.agent_response
        parsed_response = None
        if agent_response:
            try:
                parsed_response = _json.loads(agent_response)
            except Exception:
                parsed_response = agent_response
 
        # Safely convert status string to enum
        try:
            from BE.models.enums import ConversationStatus
            status = ConversationStatus(conversation.response_status)
        except (ValueError, KeyError):
            from BE.models.enums import ConversationStatus
            status = ConversationStatus.in_progress
 
        return ConversationPollResponse(
            conversation_id=conversation.conversation_id,
            session_id=conversation.session_id,
            status=status,
            user_query=conversation.user_message,
            content=parsed_response,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
 
 
 