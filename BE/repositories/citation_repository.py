"""Repository for citation data access operations."""

from datetime import datetime

from BE.auth.context import get_current_user
from BE.models.database import Citation, Document
from BE.repositories.base_repository import BaseRepository


class CitationRepository(BaseRepository):
    """Data access layer for the citations Delta table."""

    def insert_citations(self, citations: list[Citation]) -> None:
        """Batch insert citation records with audit columns.

        Sets audit columns (created_by, created_at, updated_by, updated_at,
        is_active) on each citation before adding them all to the session.

        Args:
            citations: List of Citation ORM instances to persist.
        """
        now = datetime.utcnow()
        user = get_current_user()

        for citation in citations:
            citation.created_by = user
            citation.created_at = now
            citation.updated_by = user
            citation.updated_at = now
            citation.is_active = True

        self.session.add_all(citations)
        self.session.flush()

    def get_citations_by_message(self, message_id: str) -> list[dict]:
        """Return citations for a message with document_name resolved.

        Joins Citation with Document to resolve file_name as document_name.

        Args:
            message_id: The UUID string of the session message.

        Returns:
            A list of dicts with citation_id, document_id, document_name,
            page_number, section_name, source_text.
        """
        rows = (
            self.session.query(
                Citation.citation_id,
                Citation.document_id,
                Document.file_name.label("document_name"),
                Citation.page_number,
                Citation.section_name,
                Citation.source_text,
            )
            .join(Document, Citation.document_id == Document.document_id)
            .filter(
                Citation.message_id == message_id,
                Citation.is_active == True,  # noqa: E712
            )
            .all()
        )

        return [
            {
                "citation_id": row.citation_id,
                "document_id": row.document_id,
                "document_name": row.document_name,
                "page_number": row.page_number,
                "section_name": row.section_name,
                "source_text": row.source_text,
            }
            for row in rows
        ]

    def get_citations_by_messages_batch(self, message_ids: list[str]) -> dict[str, list[dict]]:
        """Return citations for multiple messages in a single query.

        Args:
            message_ids: List of message UUID strings.

        Returns:
            A dict mapping message_id to list of citation dicts.
        """
        if not message_ids:
            return {}
        rows = (
            self.session.query(
                Citation.message_id,
                Citation.citation_id,
                Citation.document_id,
                Document.file_name.label("document_name"),
                Citation.page_number,
                Citation.section_name,
                Citation.source_text,
            )
            .join(Document, Citation.document_id == Document.document_id)
            .filter(
                Citation.message_id.in_(message_ids),
                Citation.is_active == True,  # noqa: E712
            )
            .all()
        )
        result: dict[str, list[dict]] = {}
        for row in rows:
            result.setdefault(row.message_id, []).append({
                "citation_id": row.citation_id,
                "document_id": row.document_id,
                "document_name": row.document_name,
                "page_number": row.page_number,
                "section_name": row.section_name,
                "source_text": row.source_text,
            })
        return result

    def soft_delete_citations_by_document(self, document_id: str) -> None:
        """Soft-delete all citations referencing a document using a bulk update.

        Args:
            document_id: The UUID string of the document.
        """
        from datetime import datetime
        from BE.auth.context import get_current_user

        now = datetime.utcnow()
        user = get_current_user()
        self.session.query(Citation).filter(
            Citation.document_id == document_id,
            Citation.is_active == True,  # noqa: E712
        ).update(
            {"is_active": False, "updated_by": user, "updated_at": now},
            synchronize_session="fetch",
        )
        self.session.flush()
