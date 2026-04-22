"""Standardized error response models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from BE.utils.exceptions.exceptions import AppException, ValidationException


class ErrorDetail(BaseModel):
    """Error detail payload."""

    code: str
    """Error code constant."""

    message: str
    """Human-readable error message."""

    details: dict | None = None
    """Optional additional context."""


class ErrorResponses(BaseModel):
    """Standard error response envelope."""

    status: str = "error"
    error: ErrorDetail


class ErrorResponse(BaseModel):
    """Standardised error response returned by all API error handlers."""

    error_code: str
    message: str
    details: Optional[list[dict]] = None
    trace_id: str


def create_error_response(exc: AppException, trace_id: str) -> ErrorResponse:
    """Build an ErrorResponse from an application exception.

    For ``ValidationException`` instances the invalid *fields* are included
    in the ``details`` list so the client can highlight them.
    """
    details: list[dict] | None = None

    if isinstance(exc, ValidationException) and exc.fields:
        details = [{"field": field} for field in exc.fields]

    return ErrorResponse(
        error_code=exc.error_code,
        message=exc.detail,
        details=details,
        trace_id=trace_id,
    )
