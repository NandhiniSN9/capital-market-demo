"""Repository for async conversation tracking."""

from __future__ import annotations

import uuid
from datetime import datetime

from BE.models.database import Conversation
from BE.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository):
    """Data access for the conversations table."""

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Fetch a single active conversation by ID."""
        return self.active_query(Conversation).filter(
            Conversation.conversation_id == conversation_id,
        ).first()

    def insert_conversation(self, conversation: Conversation) -> None:
        """Insert a new conversation record.

        Overrides base insert_record because conversations table
        doesn't have created_by/updated_by columns.
        """
        now = datetime.utcnow()
        conversation.conversation_id = str(uuid.uuid4())
        conversation.is_active = True
        conversation.created_at = now
        conversation.updated_at = now
        self.session.add(conversation)
        self.session.flush()

    def update_conversation(self, conversation: Conversation) -> None:
        """Update an existing conversation record."""
        conversation.updated_at = datetime.utcnow()
        self.session.flush()
