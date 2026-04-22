"""Repository for document data access operations."""

from BE.models.database import Document
from BE.repositories.base_repository import BaseRepository
from BE.utils.exceptions import DocumentNotFoundException


class DocumentRepository(BaseRepository):
    """Data access layer for the documents Delta table."""

    def get_documents_by_chat(self, chat_id: str) -> list[Document]:
        """Return all active documents for a chat.

        Args:
            chat_id: The UUID string of the parent chat.

        Returns:
            A list of active Document instances belonging to the chat.
        """
        return (
            self.active_query(Document)
            .filter(Document.chat_id == chat_id)
            .all()
        )

    def get_document(self, document_id: str, chat_id: str) -> Document | None:
        """Return a single active document validating it belongs to the chat.

        Args:
            document_id: The UUID string of the document.
            chat_id: The UUID string of the parent chat.

        Returns:
            The Document instance or None if not found/inactive.
        """
        return (
            self.active_query(Document)
            .filter(Document.document_id == document_id, Document.chat_id == chat_id)
            .first()
        )

    def insert_document(self, document: Document) -> None:
        """Insert a new document record with audit columns.

        Args:
            document: The Document ORM instance to persist.
        """
        self.insert_record(document)

    def soft_delete_document(self, document_id: str) -> None:
        """Soft-delete a document by setting is_active to False.

        Args:
            document_id: The UUID string of the document to deactivate.

        Raises:
            DocumentNotFoundException: If the document does not exist.
        """
        document = self.session.query(Document).filter(Document.document_id == document_id).first()
        if document is None:
            raise DocumentNotFoundException(f"Document not found: {document_id}")
        self.soft_delete_record(document)

    def update_status(self, document_id: str, status: str) -> None:
        """Update the processing_status of a document.

        Args:
            document_id: The UUID string of the document.
            status: The new processing status value.

        Raises:
            DocumentNotFoundException: If the document does not exist.
        """
        document = self.session.query(Document).filter(Document.document_id == document_id).first()
        if document is None:
            raise DocumentNotFoundException(f"Document not found: {document_id}")
        document.processing_status = status
        self.update_record(document)

    def update_page_count(self, document_id: str, count: int) -> None:
        """Set the page_count on a document.

        Args:
            document_id: The UUID string of the document.
            count: The number of pages in the document.

        Raises:
            DocumentNotFoundException: If the document does not exist.
        """
        document = self.session.query(Document).filter(Document.document_id == document_id).first()
        if document is None:
            raise DocumentNotFoundException(f"Document not found: {document_id}")
        document.page_count = count
        self.update_record(document)
