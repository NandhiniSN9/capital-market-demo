"""Unified exception classes — merged from Deal + RFQ agents."""

from utils.exceptions.error_codes import (
    ERR_AGENT_LOOP_EXCEEDED,
    ERR_AGENT_PROCESSING_FAILED,
    ERR_CONVERSATION_NOT_FOUND,
    ERR_CONVERSATION_PERSIST,
    ERR_DATA_RETRIEVAL,
    ERR_GUARDRAIL_VIOLATION,
    ERR_INVALID_AGENT_TYPE,
    ERR_INVALID_PERSONA,
    ERR_INVALID_SIMULATION,
    ERR_LLM_CALL,
    ERR_METADATA_LOAD,
    ERR_SCHEMA_VALIDATION,
    ERR_TOOL_CALL,
    ERR_TOOL_EXECUTION_FAILED,
)
from utils.exceptions.exceptions import (
    AgentBaseError,
    AgentLoopExceededError,
    ConversationPersistError,
    DataRetrievalError,
    DealAgentError,
    GuardrailViolationError,
    InvalidAgentTypeError,
    InvalidPersonaError,
    InvalidSimulationError,
    LLMCallError,
    MetadataLoadError,
    RTQBaseError,
    SchemaValidationError,
    ToolCallError,
)

__all__ = [
    # Error codes
    "ERR_AGENT_LOOP_EXCEEDED", "ERR_AGENT_PROCESSING_FAILED",
    "ERR_CONVERSATION_NOT_FOUND", "ERR_CONVERSATION_PERSIST",
    "ERR_DATA_RETRIEVAL", "ERR_GUARDRAIL_VIOLATION", "ERR_INVALID_AGENT_TYPE",
    "ERR_INVALID_PERSONA", "ERR_INVALID_SIMULATION", "ERR_LLM_CALL",
    "ERR_METADATA_LOAD", "ERR_SCHEMA_VALIDATION", "ERR_TOOL_CALL",
    "ERR_TOOL_EXECUTION_FAILED",
    # Exceptions
    "AgentBaseError", "AgentLoopExceededError", "ConversationPersistError",
    "DataRetrievalError", "DealAgentError", "GuardrailViolationError",
    "InvalidAgentTypeError", "InvalidPersonaError", "InvalidSimulationError",
    "LLMCallError", "MetadataLoadError", "RTQBaseError",
    "SchemaValidationError", "ToolCallError",
]
