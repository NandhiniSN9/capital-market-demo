"""Service layer for document upload and management business logic."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from BE.auth.context import get_current_user
from BE.models.database import Document
from BE.models.responses import DocumentResponse
from BE.settings import CLASSIFICATION_MAX_CHARS
from BE.utils.exceptions import DocumentNotFoundException
from BE.utils.logger import get_logger
from BE.utils.validators import sanitize_filename, validate_file_extension

if TYPE_CHECKING:
    from BE.client.databricks_llm_client import DatabricksLLMClient
    from BE.client.unity_catalog_client import UnityCatalogClient
    from BE.client.vector_search_client import VectorSearchClient
    from BE.repositories.chunk_repository import ChunkRepository
    from BE.repositories.citation_repository import CitationRepository
    from BE.repositories.document_repository import DocumentRepository

logger = get_logger(__name__)


class DocumentService:
    """Orchestrates document upload, classification, and deletion workflows."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        citation_repository: CitationRepository,
        unity_catalog_client: UnityCatalogClient,
        llm_client: DatabricksLLMClient,
        vector_search_client: VectorSearchClient,
        document_processor: Any | None = None,
    ) -> None:
        self._document_repo = document_repository
        self._chunk_repo = chunk_repository
        self._citation_repo = citation_repository
        self._uc_client = unity_catalog_client
        self._llm_client = llm_client
        self._vs_client = vector_search_client
        self._document_processor = document_processor

    @property
    def document_processor(self) -> Any | None:
        """Return the document processor (may be set after init to avoid circular deps)."""
        return self._document_processor

    @document_processor.setter
    def document_processor(self, value: Any) -> None:
        self._document_processor = value

    # ------------------------------------------------------------------
    # Validate document belongs to company
    # ------------------------------------------------------------------

    async def validate_document_company(
        self,
        company_name: str,
        files: list[Any],
    ) -> None:
        """Check that uploaded files belong to the specified company.

        Reads the first file's content preview and asks Haiku whether
        the document belongs to the given company. Raises ValidationException
        if there's a mismatch.
        """
        if not files:
            return

        file_obj = files[0]
        filename = getattr(file_obj, "filename", str(file_obj))

        # Read content preview without consuming the file
        if hasattr(file_obj, "read"):
            content = file_obj.read()
            if hasattr(content, "__await__"):
                content = await content
            # Seek back so the file can be read again later
            if hasattr(file_obj, "seek"):
                seek_result = file_obj.seek(0)
                if hasattr(seek_result, "__await__"):
                    await seek_result
            elif hasattr(file_obj, "file") and hasattr(file_obj.file, "seek"):
                file_obj.file.seek(0)
        elif hasattr(file_obj, "file"):
            content = file_obj.file.read()
            file_obj.file.seek(0)
        else:
            return  # Can't read content, skip validation

        preview = content[:500].decode("utf-8", errors="replace")

        validation_prompt = (
            f"Does this document belong to the company '{company_name}'? "
            f"Consider that company names may appear in different forms "
            f"(e.g., 'Amazon' and 'Amazon Inc.' are the same company). "
            f"Respond with ONLY 'YES' or 'NO'.\n\n"
            f"Filename: {filename}\nContent preview: {preview}"
        )
        try:
            result = await self._llm_client.invoke_haiku(validation_prompt)
            if result.strip().upper().startswith("NO"):
                from BE.utils.exceptions import ValidationException
                raise ValidationException(
                    detail=f"Document '{filename}' does not appear to belong to '{company_name}'. Please upload documents for the correct company.",
                    fields=["files"],
                )
        except ValidationException:
            raise
        except Exception:
            pass  # If validation fails for any other reason, allow the upload

    # ------------------------------------------------------------------
    # Process upload
    # ------------------------------------------------------------------

    async def process_upload(
        self,
        chat_id: str,
        files: list[Any],
        is_first_upload: bool = False,
    ) -> list[DocumentResponse]:
        """Process uploaded files: validate, store, classify, and trigger pipeline.

        For each file:
        1. Validates file extension
        2. Generates a document_id UUID
        3. Reads file content and sanitizes filename
        4. Stores file via Unity Catalog client
        5. Classifies document_category via Claude Haiku
        6. If is_first_upload, detects company_sector via Claude Haiku
        7. Inserts Document record with processing_status=pending
        8. Generates presigned_url
        9. Triggers async pipeline via document_processor if available

        Args:
            chat_id: The UUID string of the parent chat.
            files: List of uploaded file objects (with filename and read/file attributes).
            is_first_upload: Whether this is the first upload for the chat.

        Returns:
            A list of DocumentResponse objects for the uploaded documents.
        """
        results: list[DocumentResponse] = []
        company_sector: str | None = None

        for file_obj in files:
            filename = getattr(file_obj, "filename", str(file_obj))
            ext = validate_file_extension(filename)
            safe_name = sanitize_filename(filename)

            document_id = str(uuid.uuid4())

            # Read file content
            if hasattr(file_obj, "read"):
                file_content = file_obj.read()
                if hasattr(file_content, "__await__"):
                    file_content = await file_content
            elif hasattr(file_obj, "file"):
                file_content = file_obj.file.read()
            else:
                file_content = b""

            # Store file in Unity Catalog Volume
            storage_path = self._uc_client.upload_file(chat_id, document_id, ext, file_content)

            # Classify document category and extract document year via Claude Haiku
            content_preview = file_content[:CLASSIFICATION_MAX_CHARS].decode("utf-8", errors="replace")
            classification_prompt = (
                f"Analyze this document and respond with EXACTLY two lines:\n"
                f"Line 1: The document category (one of: financial_statement, legal, operational, market)\n"
                f"Line 2: The fiscal year or document year as a 4-digit number (e.g. 2025). "
                f"If no year can be determined, write UNKNOWN.\n\n"
                f"Filename: {safe_name}\nContent preview: {content_preview}\n"
                f"Respond with only the two lines, nothing else."
            )
            classification_result = await self._llm_client.invoke_haiku(classification_prompt)
            lines = [l.strip() for l in classification_result.strip().splitlines() if l.strip()]
            document_category = lines[0].lower() if lines else "market"
            document_year = lines[1] if len(lines) > 1 else "UNKNOWN"
            # Clean up year — extract just the 4-digit number
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', document_year)
            document_year = year_match.group(0) if year_match else "UNKNOWN"

            # Detect company sector on first upload
            if is_first_upload and company_sector is None:
                sector_prompt = (
                    f"Based on this document, identify the company's industry sector "
                    f"in one or two words.\nFilename: {safe_name}\n"
                    f"Content preview: {content_preview}\n"
                    f"Respond with only the sector name."
                )
                company_sector = await self._llm_client.invoke_haiku(sector_prompt)
                company_sector = company_sector.strip()

            # Insert document record
            now = datetime.utcnow()
            user = get_current_user()
            document = Document(
                document_id=document_id,
                chat_id=chat_id,
                file_name=safe_name,
                file_type=ext,
                document_category=document_category,
                storage_path=storage_path,
                processing_status="pending",
                uploaded_at=now,
            )
            self._document_repo.insert_document(document)

            # Generate presigned URLs (view + download)
            presigned_url = self._uc_client.generate_presigned_url(chat_id, document_id)
            download_url = self._uc_client.generate_download_url(chat_id, document_id)

            # Trigger async pipeline if processor is available
            if self._document_processor is not None:
                try:
                    self._document_processor.trigger_pipeline(
                        document_id,
                        storage_path=storage_path,
                        file_type=ext,
                        file_name=safe_name,
                        chat_id=chat_id,
                    )
                except Exception:
                    logger.warning(
                        "Failed to trigger pipeline for document %s",
                        document_id,
                        extra={"document_id": document_id, "chat_id": chat_id},
                    )

            results.append(
                DocumentResponse(
                    document_id=document.document_id or document_id,
                    file_name=safe_name,
                    file_type=ext,
                    document_category=document_category,
                    processing_status="pending",
                    presigned_url=presigned_url,
                    download_url=download_url,
                    uploaded_at=now,
                    created_by=document.created_by or user,
                    created_at=document.created_at or now,
                    updated_by=document.updated_by or user,
                    updated_at=document.updated_at or now,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Delete document
    # ------------------------------------------------------------------

    def delete_document(self, document_id: str, chat_id: str) -> None:
        """Soft-delete a document and clean up related chunks, citations, and vectors.

        Args:
            document_id: The UUID string of the document to delete.
            chat_id: The UUID string of the parent chat.

        Raises:
            DocumentNotFoundException: If the document does not exist or is inactive.
        """
        document = self._document_repo.get_document(document_id, chat_id)
        if document is None:
            raise DocumentNotFoundException(f"Document not found: {document_id}")

        # Soft-delete document
        self._document_repo.soft_delete_document(document_id)

        # Clean up related chunks and citations
        self._chunk_repo.soft_delete_chunks_by_document(document_id)
        self._citation_repo.soft_delete_citations_by_document(document_id)

        # Remove embeddings from vector search
        self._vs_client.delete_by_document(document_id)
