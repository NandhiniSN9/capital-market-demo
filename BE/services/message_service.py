"""Service layer for message management business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from BE.models.database import SessionMessage
from BE.utils.exceptions import (
    ChatNotFoundException,
    SessionNotFoundException,
)

if TYPE_CHECKING:
    from BE.repositories.chat_repository import ChatRepository
    from BE.repositories.citation_repository import CitationRepository
    from BE.repositories.message_repository import MessageRepository
    from BE.repositories.session_repository import SessionRepository


class MessageService:
    """Orchestrates message retrieval and persistence."""

    def __init__(
        self,
        chat_repository: ChatRepository,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
        citation_repository: CitationRepository,
    ) -> None:
        self._chat_repo = chat_repository
        self._session_repo = session_repository
        self._message_repo = message_repository
        self._citation_repo = citation_repository

    def get_session_messages(self, chat_id: str, session_id: str) -> list[dict]:
        """Return all messages for a session with citations on assistant messages.

        Validates chat and session exist and session belongs to chat.
        Fetches messages ordered by created_at, enriches assistant messages
        with citations (including document_name).

        Args:
            chat_id: The UUID string of the parent chat.
            session_id: The UUID string of the session.

        Returns:
            A list of UserMessage/AssistantMessage dicts.

        Raises:
            ChatNotFoundException: If the chat does not exist or is inactive.
            SessionNotFoundException: If the session does not exist, is inactive,
                or does not belong to the chat.
        """
        chat = self._chat_repo.get_chat(chat_id)
        if chat is None:
            raise ChatNotFoundException(f"Chat not found: {chat_id}")

        session = self._session_repo.get_session(session_id)
        if session is None or session.chat_id != chat_id:
            raise SessionNotFoundException(
                f"Session not found or does not belong to chat: {session_id}"
            )

        messages = self._message_repo.get_messages_by_session(session_id)

        # Batch-fetch citations for all assistant messages in one query
        assistant_msg_ids = [m.message_id for m in messages if m.role != "user"]
        citations_map = self._citation_repo.get_citations_by_messages_batch(assistant_msg_ids)

        result: list[dict] = []

        for msg in messages:
            if msg.role == "user":
                result.append({
                    "message_id": msg.message_id,
                    "role": "user",
                    "content": msg.content,
                    "created_at": msg.created_at,
                })
            else:
                citations = citations_map.get(msg.message_id, [])
                # Parse JSON string fields back to objects for the FE
                import json as _json
                calculations = msg.calculations
                if isinstance(calculations, str):
                    try:
                        calculations = _json.loads(calculations)
                    except Exception:
                        calculations = None
                suggested_questions = msg.suggested_questions
                if isinstance(suggested_questions, str):
                    try:
                        suggested_questions = _json.loads(suggested_questions)
                    except Exception:
                        suggested_questions = None
                result.append({
                    "message_id": msg.message_id,
                    "role": "assistant",
                    "content": msg.content,
                    "citations": citations,
                    "confidence_level": msg.confidence_level,
                    "assumptions": msg.assumptions,
                    "calculations": calculations,
                    "suggested_questions": suggested_questions,
                    "created_at": msg.created_at,
                })

        return result

    def save_user_message(self, session_id: str, content: str) -> SessionMessage:
        """Insert a user message.

        Args:
            session_id: The UUID string of the parent session.
            content: The message text content.

        Returns:
            The newly created SessionMessage instance.
        """
        return self._message_repo.insert_message(
            session_id=session_id,
            role="user",
            content=content,
        )

    def save_assistant_message(
        self,
        session_id: str,
        content: str,
        confidence_level: str | None = None,
        assumptions: str | None = None,
        calculations: list[dict] | None = None,
        suggested_questions: list[str] | None = None,
    ) -> SessionMessage:
        """Insert an assistant message with structured metadata.

        Args:
            session_id: The UUID string of the parent session.
            content: The message text content.
            confidence_level: Optional confidence level.
            assumptions: Optional assumptions text.
            calculations: Optional calculations JSON.
            suggested_questions: Optional follow-up questions.

        Returns:
            The newly created SessionMessage instance.
        """
        return self._message_repo.insert_message(
            session_id=session_id,
            role="assistant",
            content=content,
            confidence_level=confidence_level,
            assumptions=assumptions,
            calculations=calculations,
            suggested_questions=suggested_questions,
        )
