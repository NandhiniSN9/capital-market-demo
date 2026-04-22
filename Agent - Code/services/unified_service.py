"""Unified Service — routes requests to Deal or RFQ agent.

Handles conversation persistence, token logging, and error handling
in degraded mode (DB failures never block the response).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from agents.deal_agent import DealIntelligenceAgent
from agents.rtq_agent import RTQAgent
from models.rtq_models import RFQAgentRequest, RFQAgentResponse
from models.unified_models import UnifiedRequest
from repositories.databricks_repository import DatabricksRepository
from repositories.genie_repository import GenieRepository
from settings import get_settings
from utils.exceptions import ConversationPersistError, AgentBaseError
from utils.logger import logger


class UnifiedService:
    """Orchestrates the full request lifecycle for both agent types."""

    def __init__(
        self,
        rtq_agent: RTQAgent,
        deal_agent: DealIntelligenceAgent,
        db_repo: DatabricksRepository,
    ) -> None:
        self._rtq_agent = rtq_agent
        self._deal_agent = deal_agent
        self._db_repo = db_repo
        self._settings = get_settings()

    async def process(self, request: UnifiedRequest) -> dict[str, Any]:
        """Route to the correct agent and return the response."""
        logger.info("UnifiedService.process started", extra={
            "agent_type": request.agent_type,
            "conversation_id": request.conversation_id,
            "session_id": request.session_id,
        })

        await self._safe_insert_conversation(request)

        try:
            if request.agent_type == "rfq":
                result = await self._process_rfq(request)
            elif request.agent_type == "deal":
                result = await self._process_deal(request)
            else:
                raise ValueError(f"Unknown agent_type: {request.agent_type}")

            # Store only the agent_response portion for RFQ (large payload),
            # full result for deal agent.
            if request.agent_type == "rfq":
                persist_str = json.dumps(
                    result.get("agent_response", result),
                    default=str,
                )
            else:
                persist_str = json.dumps(result, default=str)

            await self._safe_update_conversation(
                request.conversation_id,
                persist_str,
            )

            logger.info("UnifiedService.process completed", extra={
                "agent_type": request.agent_type,
                "conversation_id": request.conversation_id,
            })
            return result

        except AgentBaseError as exc:
            await self._safe_log_error(request.user_id, exc)
            raise
        except Exception as exc:
            await self._safe_log_error(request.user_id, exc)
            raise

    async def process_stream(self, request: UnifiedRequest) -> AsyncGenerator[str, None]:
        """Stream SSE events for the Deal agent.

        Yields SSE-formatted lines: ``data: {json}\n\n``
        Falls back to non-streaming ``process()`` for non-deal agents.
        """
        logger.info("UnifiedService.process_stream started", extra={
            "agent_type": request.agent_type,
            "conversation_id": request.conversation_id,
        })

        if request.agent_type != "deal":
            # Non-deal agents don't support streaming yet — return full result as single event
            result = await self.process(request)
            yield f"data: {json.dumps({'type': 'done', 'metadata': result}, default=str)}\n\n"
            return

        await self._safe_insert_conversation(request)

        done_metadata: dict[str, Any] | None = None
        try:
            async for event in self._deal_agent.run_stream(
                user_query=request.user_message,
                chat_id=request.chat_id,
                analyst_type=request.analyst_type or "buy_side",
                scenario_type=request.scenario_type or "pre_earnings",
                conversation_history=[
                    {"role": h["role"], "content": h["content"]}
                    for h in request.conversation_history
                ] if request.conversation_history else None,
                session_id=request.session_id,
            ):
                if event.get("type") == "done":
                    done_metadata = event.get("metadata", {})
                    done_metadata = {
                        "agent_type": "deal",
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                        **done_metadata,
                    }
                    yield f"data: {json.dumps({'type': 'done', 'metadata': done_metadata}, default=str)}\n\n"
                else:
                    yield f"data: {json.dumps(event, default=str)}\n\n"

            # Persist after streaming completes
            if done_metadata:
                await self._safe_update_conversation(
                    request.conversation_id,
                    json.dumps(done_metadata, default=str),
                )

        except Exception as exc:
            await self._safe_log_error(request.user_id, exc)
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)[:500]})}\n\n"

        logger.info("UnifiedService.process_stream completed", extra={
            "conversation_id": request.conversation_id,
        })

    async def _process_rfq(self, request: UnifiedRequest) -> dict[str, Any]:
        """Run the RFQ agent."""
        # Fetch latest 2 conversations for this session (graceful — empty on failure)
        conversation_history = await self._db_repo.fetch_rfq_conversation_history(
            request.session_id, limit=2,
        )

        rfq_request = RFQAgentRequest(
            conversation_id=request.conversation_id,
            session_id=request.session_id,
            user_id=request.user_id,
            persona=request.persona,
            simulation=request.simulation,
            user_message=request.user_message,
            conversation_history=conversation_history,
        )
        response: RFQAgentResponse = await self._rtq_agent.run(rfq_request)

        await self._safe_log_tokens(
            request, self._settings.llm_model_name,
            response.total_input_tokens, response.total_output_tokens,
        )
        return response.model_dump()

    async def _process_deal(self, request: UnifiedRequest) -> dict[str, Any]:
        """Run the Deal agent (sync, wrapped in thread)."""
        result = await asyncio.to_thread(
            self._deal_agent.run,
            user_query=request.user_message,
            chat_id=request.chat_id,
            analyst_type=request.analyst_type or "buy_side",
            scenario_type=request.scenario_type or "pre_earnings",
            conversation_history=[
                {"role": h["role"], "content": h["content"]}
                for h in request.conversation_history
            ] if request.conversation_history else None,
            session_id=request.session_id,
        )
        return {
            "agent_type": "deal",
            "conversation_id": request.conversation_id,
            "session_id": request.session_id,
            **result,
        }

    # ── Degraded-mode persistence helpers ────────────────────────────────

    async def _safe_insert_conversation(self, request: UnifiedRequest) -> None:
        try:
            await self._db_repo.insert_conversation(
                conversation_id=request.conversation_id,
                session_id=request.session_id,
                user_message=request.user_message,
            )
        except ConversationPersistError as exc:
            logger.warning("Failed to insert conversation – degraded mode", extra={
                "conversation_id": request.conversation_id, "error": str(exc),
            })

    async def _safe_update_conversation(self, conversation_id: str, response_str: str) -> None:
        try:
            await self._db_repo.update_conversation_response(
                conversation_id=conversation_id, agent_response=response_str,
            )
        except ConversationPersistError as exc:
            logger.warning("Failed to update conversation", extra={
                "conversation_id": conversation_id, "error": str(exc),
            })

    async def _safe_log_tokens(
        self, request: UnifiedRequest, model_name: str,
        input_tokens: int, output_tokens: int,
    ) -> None:
        try:
            await self._db_repo.insert_token_consumption(
                token_id=f"TOK_{uuid.uuid4().hex[:12].upper()}",
                conversation_id=request.conversation_id,
                session_id=request.session_id,
                usage_type="follow_up",
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except Exception as exc:
            logger.warning("Failed to log tokens", extra={"error": str(exc)})

    async def _safe_log_error(self, user_id: str, exc: Exception) -> None:
        try:
            await self._db_repo.insert_error_log(
                error_id=f"ERR_{uuid.uuid4().hex[:12].upper()}",
                user_id=user_id,
                error_code=getattr(exc, "error_code", "UNI-999"),
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        except Exception as log_exc:
            logger.error("Failed to log error", extra={
                "original_error": str(exc), "log_error": str(log_exc),
            })
