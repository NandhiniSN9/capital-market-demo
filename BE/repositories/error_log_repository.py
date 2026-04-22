"""Data access layer for persisting application errors to error_logs table."""

import traceback
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from BE.models.database import ErrorLog
from BE.utils.logger import logger


def persist_error(
    db: Session,
    error_code: str,
    error_type: str,
    error_message: str,
    exc: BaseException | None = None,
    session_id: str | None = None,
    conversation_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """Insert a row into error_logs. Silently swallows its own failures to avoid error loops."""
    try:
        now = datetime.now(timezone.utc)
        error_id = f"ERR_{now.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)) if exc else None

        log = ErrorLog(
            error_id=error_id,
            session_id=session_id,
            conversation_id=conversation_id,
            user_id=user_id,
            error_code=error_code,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack,
            created_at=now,
        )
        db.add(log)
        db.commit()
    except Exception as inner:
        # Never let error logging crash the app
        logger.warning(f"Failed to persist error log: {inner}")
