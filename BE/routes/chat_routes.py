"""Chat workspace API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import JSONResponse

from BE.models.enums import AnalystType, ChatStatus
from BE.models.responses import ChatDetail, ChatWithDocuments, PaginatedChatsResponse, ChatStatusResponse
from BE.services.chat_service import ChatService
from BE.services.dependencies import get_chat_service
from BE.utils.validators import validate_uuid

router = APIRouter(tags=["chats"])


@router.get("/chats", response_model=PaginatedChatsResponse)
def list_chats(
    status_filter: Optional[str] = Query(None, alias="status"),
    analyst_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Return a paginated list of chat workspaces."""
    return chat_service.list_chats(
        status=status_filter,
        analyst_type=analyst_type,
        page=page,
        limit=limit,
    )


@router.post("/chats", status_code=status.HTTP_201_CREATED, response_model=ChatWithDocuments)
async def create_or_upload(
    company_name: Optional[str] = Form(None),
    analyst_type: Optional[str] = Form(None),
    company_url: Optional[str] = Form(None),
    chat_id: Optional[str] = Form(None),
    files: list[UploadFile] = File(default=[]),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Create a new chat workspace or upload documents to an existing one.

    Mode 1 (no chat_id): Creates a new chat. Requires company_name and analyst_type.
    Mode 2 (chat_id provided): Uploads documents to an existing chat. Requires files.
    """
    if chat_id is not None:
        # Mode 2: upload to existing chat
        validate_uuid(chat_id)
        return await chat_service.upload_documents(chat_id=chat_id, files=files)

    # Mode 1: create new chat
    from BE.utils.exceptions import ValidationException

    if not company_name:
        raise ValidationException(detail="company_name is required", fields=["company_name"])
    if not analyst_type:
        raise ValidationException(detail="analyst_type is required", fields=["analyst_type"])

    # Validate analyst_type enum
    try:
        AnalystType(analyst_type)
    except ValueError:
        raise ValidationException(
            detail=f"Invalid analyst_type: '{analyst_type}'",
            fields=["analyst_type"],
        )

    return await chat_service.create_chat(
        company_name=company_name,
        analyst_type=analyst_type,
        company_url=company_url,
        files=files if files else None,
    )


@router.get("/chats/{chat_id}", response_model=ChatDetail)
def get_chat_details(
    chat_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Return full chat details including documents and sessions."""
    validate_uuid(chat_id)
    return chat_service.get_chat_details(chat_id)

@router.get("/chats/{chat_id}/status", response_model=ChatStatusResponse)
def get_chat_status(
    chat_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Return chat processing status and per-document processing status for polling."""
    validate_uuid(chat_id)
    return chat_service.get_chat_status(chat_id)
