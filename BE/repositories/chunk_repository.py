"""Repository for document chunk data access operations."""

from datetime import datetime

from BE.auth.context import get_current_user
from BE.models.database import DocumentChunk
from BE.repositories.base_repository import BaseRepository


class ChunkRepository(BaseRepository):
    """Data access layer for the document_chunks Delta table."""

    def insert_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Batch insert document chunks with audit columns.

        Sets audit columns (created_by, created_at, updated_by, updated_at,
        is_active) on each chunk before adding them all to the session.

        Args:
            chunks: List of DocumentChunk ORM instances to persist.
        """
        now = datetime.utcnow()
        user = get_current_user()

        for chunk in chunks:
            chunk.created_by = user
            chunk.created_at = now
            chunk.updated_by = user
            chunk.updated_at = now
            chunk.is_active = True

        self.session.add_all(chunks)
        self.session.flush()

    def soft_delete_chunks_by_document(self, document_id: str) -> None:
        """Soft-delete all chunks belonging to a document using a bulk update.

        Args:
            document_id: The UUID string of the parent document.
        """
        from datetime import datetime
        from BE.auth.context import get_current_user

        now = datetime.utcnow()
        user = get_current_user()
        self.session.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.is_active == True,  # noqa: E712
        ).update(
            {"is_active": False, "updated_by": user, "updated_at": now},
            synchronize_session="fetch",
        )
        self.session.flush()

    def get_chunks_by_document(self, document_id: str) -> list[DocumentChunk]:
        """Return all active chunks for a document.

        Args:
            document_id: The UUID string of the parent document.

        Returns:
            A list of active DocumentChunk instances.
        """
        return (
            self.active_query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .all()
        )
