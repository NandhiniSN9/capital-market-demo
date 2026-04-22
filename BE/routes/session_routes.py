"""Session management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from BE.services.dependencies import get_session_service
from BE.services.session_service import DealSessionService
from BE.utils.validators import validate_uuid

router = APIRouter(tags=["sessions"])


@router.get("/chats/{chat_id}/sessions")
def list_sessions(
    chat_id: str,
    session_service: DealSessionService = Depends(get_session_service),
):
    """Return all active sessions for a chat with message counts."""
    validate_uuid(chat_id)
    sessions = session_service.list_sessions(chat_id)
    return {"sessions": sessions}
