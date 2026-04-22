"""Session and conversation endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from BE.models.db import get_db
from BE.models.schemas import (
    ConversationListResponse,
    ConversationResponse,
    SessionAckResponse,
    SessionRequest,
)
from BE.services.dependencies import get_rfq_session_service

router = APIRouter(tags=["Session"])


@router.post("/session", response_model=SessionAckResponse)
def create_or_continue_session(
    request: SessionRequest,
    db: Session = Depends(get_db),
) -> SessionAckResponse:
    """Create a new chat session or continue an existing one."""
    service = get_rfq_session_service(db)
    return service.handle_session_request(request)


@router.get("/session/{session_id}/conversations", response_model=ConversationListResponse)
def get_session_conversations(
    session_id: str,
    db: Session = Depends(get_db),
) -> ConversationListResponse:
    """Get all conversations for a session, ordered chronologically."""
    service = get_rfq_session_service(db)
    return service.get_session_conversations(session_id)


@router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
def poll_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Poll for a conversation response by conversation_id."""
    service = get_rfq_session_service(db)
    return service.poll_conversation(conversation_id)
