"""Repository for session message data access operations."""

import json

from sqlalchemy import func

from BE.models.database import SessionMessage
from BE.repositories.base_repository import BaseRepository

class MessageRepository(BaseRepository):
    """Data access layer for the session_messages Delta table."""
 
    def insert_message(
        self,
        session_id: str,
        role: str,
        content: str,
        scenario_type: str | None = None,
        confidence_level: str | None = None,
        assumptions: str | None = None,
        calculations: list[dict] | None = None,
        suggested_questions: list[str] | None = None,
    ) -> SessionMessage:
        """Create and insert a session message."""
        message = SessionMessage(
            session_id=session_id,
            role=role,
            content=content,
            scenario_type=scenario_type,
            confidence_level=confidence_level,
            assumptions=assumptions,
            calculations=json.dumps(calculations) if calculations else None,
            suggested_questions=json.dumps(suggested_questions) if suggested_questions else None,
        )
        self.insert_record(message)
        return message
 
    def get_messages_by_session(self, session_id: str) -> list[SessionMessage]:
        """Return all active messages for a session ordered by created_at ascending."""
        return (
            self.active_query(SessionMessage)
            .filter(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.created_at.asc())
            .all()
        )
 
    def get_message_count(self, session_id: str) -> int:
        """Return the count of active messages for a session."""
        return (
            self.active_query(SessionMessage)
            .filter(SessionMessage.session_id == session_id)
            .with_entities(func.count(SessionMessage.message_id))
            .scalar()
        ) or 0

    def get_message_counts_batch(self, session_ids: list[str]) -> dict[str, int]:
        """Return message counts for multiple sessions in a single query."""
        if not session_ids:
            return {}
        rows = (
            self.session.query(
                SessionMessage.session_id,
                func.count(SessionMessage.message_id),
            )
            .filter(
                SessionMessage.session_id.in_(session_ids),
                SessionMessage.is_active == True,  # noqa: E712
            )
            .group_by(SessionMessage.session_id)
            .all()
        )
        return dict(rows)
