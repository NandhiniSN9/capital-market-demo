"""Conversation polling API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from BE.models.responses import ConversationPollResponse, DealConversationResponse
from BE.services.conversation_service import ConversationService
from BE.services.dependencies import get_conversation_service
from BE.utils.validators import validate_uuid

router = APIRouter(tags=["conversations"])


@router.get("/conversations/{conversation_id}", response_model=ConversationPollResponse)
def poll_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Poll the status of an async agent conversation."""
    validate_uuid(conversation_id)
    return conversation_service.get_conversation(conversation_id)


@router.get("/deal_conversation/{conversation_id}", response_model=DealConversationResponse)
def get_deal_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Get deal conversation response with rich format."""
    validate_uuid(conversation_id)
    return conversation_service.get_deal_conversation(conversation_id)
