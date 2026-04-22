"""SQLAlchemy ORM models for Deal Intelligence Agent (Deal tables + shared conversations)."""

from databricks.sqlalchemy import TIMESTAMP
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase

from BE.settings import (
    CHATS_TABLE,
    CITATIONS_TABLE,
    DOCUMENT_CHUNKS_TABLE,
    DOCUMENTS_TABLE,
    SESSION_MESSAGES_TABLE,
    SESSIONS_TABLE,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""


class Chat(Base):
    __tablename__ = CHATS_TABLE

    chat_id = Column(String, primary_key=True)
    company_name = Column(String, nullable=False)
    company_url = Column(String, nullable=True)
    company_sector = Column(String, nullable=True)
    analyst_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    document_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Document(Base):
    __tablename__ = DOCUMENTS_TABLE

    document_id = Column(String, primary_key=True)
    chat_id = Column(String, ForeignKey(f"{CHATS_TABLE}.chat_id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    document_category = Column(String, nullable=True)
    page_count = Column(Integer, nullable=True)
    storage_path = Column(String, nullable=False)
    processing_status = Column(String, nullable=False, default="pending")
    uploaded_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class DocumentChunk(Base):
    __tablename__ = DOCUMENT_CHUNKS_TABLE

    chunk_id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey(f"{DOCUMENTS_TABLE}.document_id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_type = Column(String, nullable=False, default="text")
    page_number = Column(Integer, nullable=True)
    section_name = Column(String, nullable=True)
    embedding = Column(Text, nullable=True)
    metadata_json = Column("metadata", Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Session(Base):
    __tablename__ = SESSIONS_TABLE

    session_id = Column(String, primary_key=True)
    chat_id = Column(String, ForeignKey(f"{CHATS_TABLE}.chat_id"), nullable=False)
    session_title = Column(String, nullable=True)
    agent_type = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class SessionMessage(Base):
    __tablename__ = SESSION_MESSAGES_TABLE

    message_id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey(f"{SESSIONS_TABLE}.session_id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    scenario_type = Column(String, nullable=True)
    confidence_level = Column(String, nullable=True)
    assumptions = Column(Text, nullable=True)
    calculations = Column(Text, nullable=True)
    suggested_questions = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Citation(Base):
    __tablename__ = CITATIONS_TABLE

    citation_id = Column(String, primary_key=True)
    message_id = Column(String, ForeignKey(f"{SESSION_MESSAGES_TABLE}.message_id"), nullable=False)
    document_id = Column(String, ForeignKey(f"{DOCUMENTS_TABLE}.document_id"), nullable=False)
    chunk_id = Column(String, ForeignKey(f"{DOCUMENT_CHUNKS_TABLE}.chunk_id"), nullable=False)
    page_number = Column(Integer, nullable=True)
    section_name = Column(String, nullable=True)
    source_text = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Conversation(Base):
    """Shared conversations table — used by both Deal and RFQ agents."""
    __tablename__ = "conversations"

    conversation_id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    user_message = Column(String)
    agent_response = Column(String)
    response_status = Column(String, default="in_progress")
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
