"""Message and conversation API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from BE.models.requests import SendMessageRequest
from BE.models.responses import ConversationResponse
from BE.services.conversation_service import ConversationService
from BE.services.dependencies import get_conversation_service, get_message_service
from BE.services.message_service import MessageService
from BE.utils.validators import validate_uuid

router = APIRouter(tags=["messages"])


@router.post(
    "/chats/{chat_id}/messages",
    response_model=ConversationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def send_message(
    chat_id: str,
    request: SendMessageRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Accept a user message, save it, and create a conversation for async processing."""
    validate_uuid(chat_id)
    return conversation_service.create_conversation(chat_id, request)


@router.get("/chats/{chat_id}/sessions/{session_id}/messages")
def get_session_messages(
    chat_id: str,
    session_id: str,
    message_service: MessageService = Depends(get_message_service),
):
    """Return the full conversation history for a session."""
    validate_uuid(chat_id)
    validate_uuid(session_id)
    messages = message_service.get_session_messages(chat_id, session_id)
    return {"messages": messages}
