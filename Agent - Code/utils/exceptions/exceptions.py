"""Unified exception hierarchy — merged from Deal + RFQ agents."""


class AgentBaseError(Exception):
    """Root exception for all agent errors (both Deal and RFQ)."""

    def __init__(self, message: str, error_code: str = "") -> None:
        super().__init__(message)
        self.error_code = error_code


# ── Unified ──────────────────────────────────────────────────────────────
class InvalidAgentTypeError(AgentBaseError):
    """Raised when an unsupported agent_type is supplied."""


# ── RFQ exceptions ───────────────────────────────────────────────────────
class RTQBaseError(AgentBaseError):
    """Base for RFQ-specific errors."""


class InvalidPersonaError(RTQBaseError):
    pass


class InvalidSimulationError(RTQBaseError):
    pass


class GuardrailViolationError(RTQBaseError):
    pass


class MetadataLoadError(RTQBaseError):
    pass


class DataRetrievalError(RTQBaseError):
    pass


class ToolCallError(RTQBaseError):
    pass


class LLMCallError(RTQBaseError):
    pass


class AgentLoopExceededError(RTQBaseError):
    pass


class SchemaValidationError(RTQBaseError):
    pass


class ConversationPersistError(RTQBaseError):
    pass


# ── Deal exceptions ─────────────────────────────────────────────────────
class DealAgentError(AgentBaseError):
    """Base for Deal-specific errors."""
