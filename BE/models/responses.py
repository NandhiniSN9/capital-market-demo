"""Pydantic v2 response models for the Deal Intelligence Agent API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import UUID4, BaseModel, ConfigDict

from BE.models.enums import (
    AgentType,
    AnalystType,
    ChatStatus,
    ConfidenceLevel,
    ConversationStatus,
    DocumentCategory,
    FileType,
    ProcessingStatus,
    ScenarioType,
)


class ChatSummary(BaseModel):
    """Summary of a chat workspace for list views."""

    model_config = ConfigDict(from_attributes=True)

    chat_id: UUID4
    company_name: str
    company_sector: Optional[str] = None
    analyst_type: AnalystType
    status: ChatStatus
    document_count: int
    session_count: int
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime


class PaginatedChatsResponse(BaseModel):
    """Paginated list of chat summaries."""

    chats: list[ChatSummary]
    total: int
    page: int
    limit: int


class DocumentResponse(BaseModel):
    """Document details returned in API responses (excludes storage_path)."""

    model_config = ConfigDict(from_attributes=True)

    document_id: UUID4
    file_name: str
    file_type: FileType
    document_category: Optional[DocumentCategory] = None
    processing_status: ProcessingStatus
    presigned_url: Optional[str] = None
    """Time-limited URL for viewing the document inline."""
    download_url: Optional[str] = None
    """Time-limited URL for downloading the document as an attachment."""
    uploaded_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime


class ChatWithDocuments(BaseModel):
    """Chat workspace with its associated documents."""

    model_config = ConfigDict(from_attributes=True)

    chat_id: UUID4
    company_name: str
    company_url: Optional[str] = None
    company_sector: Optional[str] = None
    analyst_type: AnalystType
    status: ChatStatus
    document_count: int
    documents: list[DocumentResponse]
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime


class SessionSummary(BaseModel):
    """Summary of a conversation session."""

    model_config = ConfigDict(from_attributes=True)

    session_id: UUID4
    session_title: Optional[str] = None
    agent_type: Optional[AgentType] = None
    message_count: int
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime


class ChatDetail(BaseModel):
    """Full chat details including documents and sessions."""

    model_config = ConfigDict(from_attributes=True)

    chat_id: UUID4
    company_name: str
    company_url: Optional[str] = None
    company_sector: Optional[str] = None
    analyst_type: AnalystType
    status: ChatStatus
    document_count: int
    documents: list[DocumentResponse]
    sessions: list[SessionSummary]
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime


class CitationResponse(BaseModel):
    """Citation linking agent response to source document."""

    model_config = ConfigDict(from_attributes=True)

    citation_id: UUID4
    document_id: UUID4
    document_name: Optional[str] = None
    page_number: Optional[int] = None
    section_name: Optional[str] = None
    source_text: Optional[str] = None


class UserMessage(BaseModel):
    """User message in a conversation session."""

    model_config = ConfigDict(from_attributes=True)

    message_id: UUID4
    role: str = "user"
    content: str
    created_at: datetime


class AssistantMessage(BaseModel):
    """Assistant message with citations and structured metadata."""

    model_config = ConfigDict(from_attributes=True)

    message_id: UUID4
    role: str = "assistant"
    content: str
    citations: list[CitationResponse] = []
    confidence_level: Optional[ConfidenceLevel] = None
    assumptions: Optional[str] = None
    calculations: Optional[list[dict]] = None
    suggested_questions: Optional[list[str]] = None
    created_at: datetime


class AgentResponse(BaseModel):
    """Response from the AI agent for a user message."""

    model_config = ConfigDict(from_attributes=True)

    message_id: UUID4
    session_id: UUID4
    role: str = "assistant"
    content: str
    citations: list[CitationResponse] = []
    confidence_level: Optional[ConfidenceLevel] = None
    assumptions: Optional[str] = None
    calculations: Optional[list[dict]] = None
    suggested_questions: Optional[list[str]] = None
    created_by: str
    created_at: datetime


class ConversationResponse(BaseModel):
    """Immediate 202 response when a message is submitted for async processing."""

    conversation_id: UUID4
    session_id: UUID4
    status: ConversationStatus = ConversationStatus.in_progress
    message: str = "Your question is being processed. Poll the conversation endpoint for results."
    created_at: datetime


class ConversationPollResponse(BaseModel):
    """Response from the polling endpoint for async agent conversations."""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID4
    session_id: UUID4
    status: ConversationStatus
    user_query: Optional[str] = None
    content: Optional[Any] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DealCitationResponse(BaseModel):
    """Citation in the deal conversation response."""
    citation_id: Optional[str] = None
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    short_name: Optional[str] = None
    page_number: Optional[int] = None
    section_name: Optional[str] = None
    source_text: Optional[str] = None
    label: Optional[str] = None


class DealCalculation(BaseModel):
    """Calculation step in the deal conversation response."""
    title: Optional[str] = None
    steps: Optional[str] = None
    result: Optional[str] = None


class DealSourceExcerpt(BaseModel):
    """Source excerpt in the deal conversation response."""
    citation_id: Optional[str] = None
    text: Optional[str] = None
    context: Optional[str] = None


class DealConversationResponse(BaseModel):
    """Rich response for the deal conversation endpoint."""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID4
    session_id: UUID4
    status: ConversationStatus
    user_query: Optional[str] = None
    analyst_type: Optional[str] = None
    content: Optional[Any] = None
    confidence_level: Optional[str] = None
    confidence_reason: Optional[str] = None
    citations: Optional[list[DealCitationResponse]] = None
    calculations: Optional[list[DealCalculation]] = None
    source_excerpts: Optional[list[DealSourceExcerpt]] = None
    assumptions: Optional[list[str]] = None
    suggested_questions: Optional[list[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error_code: str
    message: str
    details: Optional[list[dict]] = None
    trace_id: str

class ChatStatusResponse(BaseModel):
    """Response for the chat status polling endpoint."""
 
    status: str = "success"
    chat_id: str
    chat_status: str
