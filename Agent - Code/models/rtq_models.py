"""Request / response / state models for the RFQ agent."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RFQAgentRequest(BaseModel):
    """Internal RFQ agent request (mapped from UnifiedRequest)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    conversation_id: str
    session_id: str
    user_id: str
    persona: str
    simulation: str
    user_message: str
    conversation_history: list[dict[str, str]] = Field(default_factory=list)


class MetadataResource(BaseModel):
    tables: dict[str, Any]
    formulas: dict[str, Any] = Field(default_factory=dict)


class ToolCallLog(BaseModel):
    tool_name: str
    input_summary: str
    output_summary: str
    duration_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    success: bool = True
    error_message: str = ""


class DataExtraction(BaseModel):
    language: str = Field(..., description="Query language, e.g. 'sql'")
    query: str = Field(..., description="Raw query string")


class KeyDataPoint(BaseModel):
    label: str
    value: str


class RawData(BaseModel):
    columns: list[str]
    rows: list[list[Any]]


class Source(BaseModel):
    id: int
    panel: str
    type: str
    latency: str
    title: str
    description: str
    data_extraction: DataExtraction
    key_data_points: list[KeyDataPoint]
    raw_data: Optional[RawData] = None
    methodology: str
    last_updated: str


class Panel(BaseModel):
    panel_id: str
    label: str
    description: Optional[str] = None
    collapsed: bool = True
    icon: Optional[Literal["plan", "calendar", "compliance", "metrics"]] = None
    columns: Optional[list[str]] = None
    rows: Optional[list[list[Any]]] = None
    content: Optional[str] = None


class AgentResponsePayload(BaseModel):
    response_message: str
    confidence: int = Field(..., ge=0, le=100)
    panels: Optional[list[Panel]] = None
    sources: Optional[list[Source]] = None
    recommendations: list[str] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)


class AgentResponseEnvelope(BaseModel):
    agent_response: AgentResponsePayload


class RFQAgentResponse(BaseModel):
    conversation_id: str
    session_id: str
    persona: str
    simulation: str
    agent_response: AgentResponsePayload
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    tool_logs: list[ToolCallLog] = Field(default_factory=list)
    prompt_version: str = "v1"
 