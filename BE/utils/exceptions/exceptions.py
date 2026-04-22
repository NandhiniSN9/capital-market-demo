"""Custom exception classes."""

from BE.utils.exceptions.error_codes import (
    CHAT_NOT_FOUND,
    DOCUMENT_NOT_FOUND,
    INTERNAL_ERROR,
    SESSION_NOT_FOUND,
    VALIDATION_ERROR,
)



class AppException(Exception):
    """Base exception for all application-specific errors."""

    def __init__(
        self,
        detail: str,
        error_code: str = INTERNAL_ERROR,
        status_code: int = 500,
    ) -> None:
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(detail)


class ChatNotFoundException(AppException):
    """Raised when a chat does not exist or is inactive."""

    def __init__(
        self,
        detail: str = "Chat not found",
        error_code: str = CHAT_NOT_FOUND,
    ) -> None:
        super().__init__(detail=detail, error_code=error_code, status_code=404)


class DocumentNotFoundException(AppException):
    """Raised when a document does not exist or is inactive."""

    def __init__(
        self,
        detail: str = "Document not found",
        error_code: str = DOCUMENT_NOT_FOUND,
    ) -> None:
        super().__init__(detail=detail, error_code=error_code, status_code=404)


class SessionNotFoundException(AppException):
    """Raised when a session does not exist or does not belong to the chat."""

    def __init__(
        self,
        detail: str = "Session not found",
        error_code: str = SESSION_NOT_FOUND,
    ) -> None:
        super().__init__(detail=detail, error_code=error_code, status_code=404)


class ValidationException(AppException):
    """Raised when request validation fails."""

    def __init__(
        self,
        detail: str = "Validation error",
        error_code: str = VALIDATION_ERROR,
        fields: list[str] | None = None,
    ) -> None:
        self.fields: list[str] = fields or []
        super().__init__(detail=detail, error_code=error_code, status_code=422)


class ProcessingException(AppException):
    """Raised when an internal processing error occurs."""

    def __init__(
        self,
        detail: str = "Internal processing error",
        error_code: str = INTERNAL_ERROR,
    ) -> None:
        super().__init__(detail=detail, error_code=error_code, status_code=500)

class RFQDashboardException(Exception):
    """Base exception for the RFQ Dashboard application."""

    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class InvalidParamsException(RFQDashboardException):
    """Raised when request parameters are invalid."""

    def __init__(self, message: str):
        super().__init__(message=message, error_code="INVALID_PARAMS", status_code=400)


class TraderNotFoundException(RFQDashboardException):
    """Raised when a trader is not found."""

    def __init__(self, trader_id: str):
        super().__init__(
            message=f"Trader not found: {trader_id}",
            error_code="TRADER_NOT_FOUND",
            status_code=400,
        )


class RFQSessionNotFoundException(RFQDashboardException):
    """Raised when an RFQ session is not found."""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session not found: {session_id}",
            error_code="SESSION_NOT_FOUND",
            status_code=400,
        )


class ConversationNotFoundException(RFQDashboardException):
    """Raised when a conversation is not found."""

    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversation not found: {conversation_id}",
            error_code="CONVERSATION_NOT_FOUND",
            status_code=400,
        )


class DatabaseException(RFQDashboardException):
    """Raised when a database operation fails (connection, permissions, query errors)."""

    def __init__(self, message: str = "A database error occurred — please try again later"):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=503,
        )
