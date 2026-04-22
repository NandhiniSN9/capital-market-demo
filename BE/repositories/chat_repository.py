"""Repository for chat workspace data access operations."""

from sqlalchemy import func, literal_column, over
from sqlalchemy.orm import aliased

from BE.models.database import Chat, Document, Session
from BE.repositories.base_repository import BaseRepository


class ChatRepository(BaseRepository):
    """Data access layer for the chats Delta table."""

    def get_chats_paginated(
        self,
        status: str | None,
        analyst_type: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[Chat], int]:
        """Return a paginated list of active chats with computed counts.

        Uses a single query with correlated subqueries to fetch chats,
        document counts, session counts, and total count together —
        minimising round-trips to the Databricks SQL Warehouse.
        """
        # Correlated subqueries for counts
        doc_count_sq = (
            self.session.query(func.count(Document.document_id))
            .filter(Document.chat_id == Chat.chat_id, Document.is_active == True)  # noqa: E712
            .correlate(Chat)
            .scalar_subquery()
            .label("doc_count")
        )

        session_count_sq = (
            self.session.query(func.count(Session.session_id))
            .filter(Session.chat_id == Chat.chat_id, Session.is_active == True)  # noqa: E712
            .correlate(Chat)
            .scalar_subquery()
            .label("sess_count")
        )

        query = (
            self.session.query(Chat, doc_count_sq, session_count_sq)
            .filter(Chat.is_active == True)  # noqa: E712
        )

        if status is not None:
            query = query.filter(Chat.status == status)
        if analyst_type is not None:
            query = query.filter(Chat.analyst_type == analyst_type)

        total = query.count()

        offset = (page - 1) * limit
        rows = query.offset(offset).limit(limit).all()

        chats = []
        for chat, doc_count, sess_count in rows:
            chat.document_count = doc_count or 0
            chat.session_count = sess_count or 0
            chats.append(chat)

        return chats, total

    def get_chat(self, chat_id: str) -> Chat | None:
        """Return a single active chat by ID, or None if not found.

        Args:
            chat_id: The UUID string of the chat to retrieve.

        Returns:
            The Chat instance or None.
        """
        return self.active_query(Chat).filter(Chat.chat_id == chat_id).first()

    def insert_chat(self, chat: Chat) -> None:
        """Insert a new chat record with audit columns.

        Args:
            chat: The Chat ORM instance to persist.
        """
        self.insert_record(chat)

    def update_chat(self, chat: Chat) -> None:
        """Update an existing chat record's audit columns.

        Args:
            chat: The Chat ORM instance with modified fields.
        """
        self.update_record(chat)

    def decrement_document_count(self, chat_id: str) -> None:
        """Decrement the document_count on a chat (minimum 0).

        Fetches the chat, decrements the count, and updates audit columns.

        Args:
            chat_id: The UUID string of the chat to update.
        """
        chat = self.get_chat(chat_id)
        if chat is not None:
            chat.document_count = max(0, (chat.document_count or 0) - 1)
            self.update_record(chat)
