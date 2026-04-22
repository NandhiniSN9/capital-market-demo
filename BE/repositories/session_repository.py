"""Data access layer for Deal sessions."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session as DBSession

from BE.models.database import Session
from BE.auth.context import get_current_user
from BE.utils.exceptions import DatabaseException
from BE.utils.logger import get_logger

logger = get_logger(__name__)


class SessionRepository:
    """Repository for Deal session database operations."""

    def __init__(self, db: DBSession):
        self.db = db
        self.session = db

    def get_session(self, session_id: str) -> Session | None:
        """Fetch a Deal session by ID."""
        try:
            stmt = select(Session).where(
                Session.session_id == session_id,
                Session.is_active.is_(True),
            )
            return self.db.execute(stmt).scalar_one_or_none()
        except DatabaseError as e:
            logger.error(f"DB error fetching session={session_id}: {e}")
            raise DatabaseException() from e

    def get_sessions_by_chat(self, chat_id: str) -> list[Session]:
        """Fetch all active sessions for a chat."""
        try:
            stmt = (
                select(Session)
                .where(
                    Session.chat_id == chat_id,
                    Session.is_active.is_(True),
                )
                .order_by(Session.created_at.asc())
            )
            return list(self.db.execute(stmt).scalars().all())
        except DatabaseError as e:
            logger.error(f"DB error fetching sessions for chat={chat_id}: {e}")
            raise DatabaseException() from e

    def create_session(
        self,
        chat_id: str,
        session_title: str | None = None,
        agent_type: str | None = None,
    ) -> Session:
        """Insert a new Deal session row."""
        try:
            now = datetime.now(timezone.utc)
            new_id = str(uuid.uuid4())
            user = get_current_user()
            session = Session(
                session_id=new_id,
                chat_id=chat_id,
                session_title=session_title,
                agent_type=agent_type,
                is_active=True,
                created_by=user,
                created_at=now,
                updated_by=user,
                updated_at=now,
            )
            self.db.add(session)
            self.db.flush()
            return session
        except DatabaseError as e:
            logger.error(f"DB error creating session: {e}")
            raise DatabaseException() from e
