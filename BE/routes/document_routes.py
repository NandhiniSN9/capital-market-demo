"""Document management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from BE.client.unity_catalog_client import UnityCatalogClient
from BE.repositories.document_repository import DocumentRepository
from BE.services.chat_service import ChatService
from BE.services.dependencies import get_chat_service, get_document_repository, get_unity_catalog_client
from BE.utils.exceptions import DocumentNotFoundException
from BE.utils.validators import validate_uuid

router = APIRouter(tags=["documents"])


@router.delete("/chats/{chat_id}/documents/{document_id}")
def delete_document(
    chat_id: str,
    document_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Soft-delete a document and all related data (chunks, citations, embeddings)."""
    validate_uuid(chat_id)
    validate_uuid(document_id)
    chat_service.delete_document(chat_id, document_id)
    return {"message": "Document deleted", "document_id": document_id}


MIME_TYPES = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("/chats/{chat_id}/documents/{document_id}/file")
def get_document_file(
    chat_id: str,
    document_id: str,
    mode: str = Query("view", regex="^(view|download)$"),
    document_repo: DocumentRepository = Depends(get_document_repository),
    uc_client: UnityCatalogClient = Depends(get_unity_catalog_client),
):
    """Proxy a document file from Unity Catalog Volume for viewing or downloading."""
    validate_uuid(chat_id)
    validate_uuid(document_id)

    document = document_repo.get_document(document_id, chat_id)
    if document is None:
        raise DocumentNotFoundException(f"Document not found: {document_id}")

    file_content = uc_client.read_file(document.storage_path)
    content_type = MIME_TYPES.get(document.file_type, "application/octet-stream")

    if mode == "download":
        disposition = f'attachment; filename="{document.file_name}"'
    else:
        disposition = "inline"

    return Response(
        content=file_content,
        media_type=content_type,
        headers={"Content-Disposition": disposition},
    )
