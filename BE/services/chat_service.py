"""Service layer for chat workspace business logic."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from BE.models.database import Chat
from BE.models.responses import (
    ChatDetail,
    ChatSummary,
    ChatWithDocuments,
    DocumentResponse,
    PaginatedChatsResponse,
    SessionSummary,
)
from BE.settings import DEMO_COMPANY_SECTORS
from BE.utils.exceptions import (
    ChatNotFoundException,
    DocumentNotFoundException,
)
from BE.utils.logger import get_logger

if TYPE_CHECKING:
    from BE.client.unity_catalog_client import UnityCatalogClient
    from BE.client.vector_search_client import VectorSearchClient
    from BE.repositories.chat_repository import ChatRepository

logger = get_logger(__name__)


class ChatService:
    """Orchestrates chat workspace operations.

    Coordinates between repositories and external clients to implement
    chat CRUD, document upload, and document deletion workflows.
    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        document_repository: Any,
        document_service: Any,
        session_repository: Any,
        message_repository: Any,
        unity_catalog_client: UnityCatalogClient,
        vector_search_client: VectorSearchClient,
        chunk_repository: Any,
        citation_repository: Any,
    ) -> None:
        self._chat_repo = chat_repository
        self._document_repo = document_repository
        self._document_service = document_service
        self._session_repo = session_repository
        self._message_repo = message_repository
        self._uc_client = unity_catalog_client
        self._vs_client = vector_search_client
        self._chunk_repo = chunk_repository
        self._citation_repo = citation_repository

    # ------------------------------------------------------------------
    # List chats
    # ------------------------------------------------------------------

    def list_chats(
        self,
        status: str | None,
        analyst_type: str | None,
        page: int,
        limit: int,
    ) -> PaginatedChatsResponse:
        """Return a paginated list of chat summaries.

        Args:
            status: Optional status filter (active/in_progress/completed/failed).
            analyst_type: Optional analyst type filter.
            page: 1-based page number.
            limit: Results per page.

        Returns:
            A PaginatedChatsResponse with chat summaries and pagination metadata.
        """
        chats, total = self._chat_repo.get_chats_paginated(status, analyst_type, page, limit)

        chat_summaries = [
            ChatSummary(
                chat_id=chat.chat_id,
                company_name=chat.company_name,
                company_sector=chat.company_sector,
                analyst_type=chat.analyst_type,
                status=chat.status,
                document_count=chat.document_count or 0,
                session_count=getattr(chat, "session_count", 0) or 0,
                created_by=chat.created_by,
                created_at=chat.created_at,
                updated_by=chat.updated_by,
                updated_at=chat.updated_at,
            )
            for chat in chats
        ]

        return PaginatedChatsResponse(
            chats=chat_summaries,
            total=total,
            page=page,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Create chat
    # ------------------------------------------------------------------

    async def create_chat(
        self,
        company_name: str,
        analyst_type: str,
        company_url: str | None = None,
        files: list[Any] | None = None,
    ) -> ChatWithDocuments:
        """Create a new chat workspace and optionally process uploaded files.

        Args:
            company_name: The company name for the workspace.
            analyst_type: The analyst role type.
            company_url: Optional company URL.
            files: Optional list of uploaded file objects.

        Returns:
            A ChatWithDocuments response with the new chat and any documents.
        """
        chat = Chat(
            company_name=company_name,
            analyst_type=analyst_type,
            company_url=company_url,
            company_sector=DEMO_COMPANY_SECTORS.get(company_name),
            status="active",
            document_count=0,
        )

        # Validate documents belong to the company before creating the chat
        if files:
            await self._document_service.validate_document_company(company_name, files)

        self._chat_repo.insert_chat(chat)
        # Commit immediately so the chat record is visible to the document pipeline
        self._chat_repo.session.commit()

        documents: list[DocumentResponse] = []
        if files:
            documents = await self._document_service.process_upload(chat.chat_id, files)
            chat.document_count = len(documents)
            chat.status = "in_progress"
            self._chat_repo.update_chat(chat)

        return ChatWithDocuments(
            chat_id=chat.chat_id,
            company_name=chat.company_name,
            company_url=chat.company_url,
            company_sector=chat.company_sector,
            analyst_type=chat.analyst_type,
            status=chat.status,
            document_count=chat.document_count or 0,
            documents=documents,
            created_by=chat.created_by,
            created_at=chat.created_at,
            updated_by=chat.updated_by,
            updated_at=chat.updated_at,
        )

    # ------------------------------------------------------------------
    # Get chat details
    # ------------------------------------------------------------------

    def get_chat_details(self, chat_id: str) -> ChatDetail:
        """Fetch full chat details including documents and sessions.

        Args:
            chat_id: The UUID string of the chat.

        Returns:
            A ChatDetail response with documents (fresh presigned URLs) and sessions.

        Raises:
            ChatNotFoundException: If the chat does not exist or is inactive.
        """
        chat = self._chat_repo.get_chat(chat_id)
        if chat is None:
            raise ChatNotFoundException(f"Chat not found: {chat_id}")

        # Fetch active documents with fresh presigned URLs
        raw_documents = self._document_repo.get_documents_by_chat(chat_id)
        documents = []
        for doc in raw_documents:
            presigned_url = self._uc_client.generate_presigned_url(chat_id, doc.document_id)
            download_url = self._uc_client.generate_download_url(chat_id, doc.document_id)
            documents.append(
                DocumentResponse(
                    document_id=doc.document_id,
                    file_name=doc.file_name,
                    file_type=doc.file_type,
                    document_category=doc.document_category,
                    processing_status=doc.processing_status,
                    presigned_url=presigned_url,
                    download_url=download_url,
                    uploaded_at=doc.uploaded_at,
                    created_by=doc.created_by,
                    created_at=doc.created_at,
                    updated_by=doc.updated_by,
                    updated_at=doc.updated_at,
                )
            )

        # Fetch active sessions with message counts (batched)
        raw_sessions = self._session_repo.get_sessions_by_chat(chat_id)
        session_ids = [s.session_id for s in raw_sessions]
        message_counts = self._message_repo.get_message_counts_batch(session_ids)
        sessions = [
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
            for sess in raw_sessions
        ]

        return ChatDetail(
            chat_id=chat.chat_id,
            company_name=chat.company_name,
            company_url=chat.company_url,
            company_sector=chat.company_sector,
            analyst_type=chat.analyst_type,
            status=chat.status,
            document_count=chat.document_count or 0,
            documents=documents,
            sessions=sessions,
            created_by=chat.created_by,
            created_at=chat.created_at,
            updated_by=chat.updated_by,
            updated_at=chat.updated_at,
        )

    # ------------------------------------------------------------------
    # Upload documents to existing chat
    # ------------------------------------------------------------------

    async def upload_documents(
        self,
        chat_id: str,
        files: list[Any],
    ) -> ChatWithDocuments:
        """Upload documents to an existing chat workspace.

        Args:
            chat_id: The UUID string of the target chat.
            files: List of uploaded file objects.

        Returns:
            A ChatWithDocuments response with the updated chat and new documents.

        Raises:
            ChatNotFoundException: If the chat does not exist or is inactive.
        """
        chat = self._chat_repo.get_chat(chat_id)
        if chat is None:
            raise ChatNotFoundException(f"Chat not found: {chat_id}")

        # Validate documents belong to the company before processing
        await self._document_service.validate_document_company(chat.company_name, files)

        documents = await self._document_service.process_upload(chat.chat_id, files)
        chat.document_count = (chat.document_count or 0) + len(documents)
        chat.status = "in_progress"
        self._chat_repo.update_chat(chat)

        return ChatWithDocuments(
            chat_id=chat.chat_id,
            company_name=chat.company_name,
            company_url=chat.company_url,
            company_sector=chat.company_sector,
            analyst_type=chat.analyst_type,
            status=chat.status,
            document_count=chat.document_count or 0,
            documents=documents,
            created_by=chat.created_by,
            created_at=chat.created_at,
            updated_by=chat.updated_by,
            updated_at=chat.updated_at,
        )

    def get_chat_status(self, chat_id: str) -> "ChatStatusResponse":
            """Return chat status for polling."""
            from BE.utils.exceptions import ChatNotFoundException
            from BE.models.responses import ChatStatusResponse
    
            chat = self._chat_repo.get_chat(chat_id)
            if chat is None:
                raise ChatNotFoundException(f"Chat not found: {chat_id}")
    
            return ChatStatusResponse(
                chat_id=chat_id,
                chat_status=chat.status,
            )
    
    # ------------------------------------------------------------------
    # Delete document (cascading soft-delete)
    # ------------------------------------------------------------------

    def delete_document(self, chat_id: str, document_id: str) -> None:
        """Perform cascading soft-delete of a document and related data.

        Soft-deletes the document, its chunks, and citations. Removes
        embeddings from Vector Search and deletes the physical file.
        Decrements the parent chat's document_count.

        Args:
            chat_id: The UUID string of the parent chat.
            document_id: The UUID string of the document to delete.

        Raises:
            ChatNotFoundException: If the chat does not exist or is inactive.
            DocumentNotFoundException: If the document does not exist or is inactive.
        """
        chat = self._chat_repo.get_chat(chat_id)
        if chat is None:
            raise ChatNotFoundException(f"Chat not found: {chat_id}")

        document = self._document_repo.get_document(document_id, chat_id)
        if document is None:
            raise DocumentNotFoundException(f"Document not found: {document_id}")

        storage_path = document.storage_path

        # Cascading soft-delete
        self._document_repo.soft_delete_document(document_id)

        try:
            self._chunk_repo.soft_delete_chunks_by_document(document_id)
        except Exception as e:
            logger.warning("Failed to soft-delete chunks for document %s: %s", document_id, str(e))

        try:
            self._citation_repo.soft_delete_citations_by_document(document_id)
        except Exception as e:
            logger.warning("Failed to soft-delete citations for document %s: %s", document_id, str(e))

        # Remove from vector search index (may fail for Delta sync indexes)
        try:
            self._vs_client.delete_by_document(document_id)
        except Exception as e:
            logger.warning("Failed to delete vector embeddings for document %s: %s", document_id, str(e))

        # Delete physical file from Unity Catalog Volume
        try:
            self._uc_client.delete_file(storage_path)
        except Exception as e:
            logger.warning("Failed to delete file for document %s: %s", document_id, str(e))

        # Decrement document count on parent chat
        self._chat_repo.decrement_document_count(chat_id)
