"""Business logic for Deal session operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from BE.models.database import Session
from BE.models.responses import SessionSummary
from BE.utils.exceptions import ChatNotFoundException

if TYPE_CHECKING:
    from BE.repositories.chat_repository import ChatRepository
    from BE.repositories.message_repository import MessageRepository
    from BE.repositories.session_repository import SessionRepository


class DealSessionService:
    """Orchestrates session-related operations."""

    def __init__(
        self,
        chat_repository: ChatRepository,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
    ) -> None:
        self._chat_repo = chat_repository
        self._session_repo = session_repository
        self._message_repo = message_repository

    def list_sessions(self, chat_id: str) -> list[SessionSummary]:
        """Return all sessions for a chat with message counts."""
        chat = self._chat_repo.get_chat(chat_id)
        if chat is None:
            raise ChatNotFoundException(f"Chat not found: {chat_id}")

        sessions = self._session_repo.get_sessions_by_chat(chat_id)
        session_ids = [s.session_id for s in sessions]
        message_counts = self._message_repo.get_message_counts_batch(session_ids)

        return [
            SessionSummary(
                session_id=sess.session_id,
                session_title=sess.session_title,
                agent_type=sess.agent_type,
                message_count=message_counts.get(sess.session_id, 0),
                created_by=sess.created_by,
                created_at=sess.created_at,
                updated_by=sess.updated_by,
                updated_at=sess.updated_at,
            )
            for sess in sessions
        ]

    def create_session(
        self,
        chat_id: str,
        session_title: str | None,
        agent_type: str | None,
    ) -> Session:
        """Create a new session in a chat."""
        return self._session_repo.create_session(chat_id, session_title, agent_type)
