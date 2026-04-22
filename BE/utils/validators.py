"""Input sanitization and validation helpers."""

from __future__ import annotations

import uuid

from BE.settings import ALLOWED_FILE_EXTENSIONS
from BE.utils.exceptions.error_codes import INVALID_FILE_TYPE, INVALID_UUID_FORMAT
from BE.utils.exceptions.exceptions import ValidationException

# Maximum filename length (common filesystem limit)
_MAX_FILENAME_LENGTH = 255


def sanitize_filename(name: str) -> str:
    """Sanitize a user-provided filename to prevent path traversal attacks.

    Strips directory separators (``/``, ``\\``), removes null bytes,
    limits length to 255 characters, and strips leading/trailing
    whitespace and dots.
    """
    # Remove null bytes
    name = name.replace("\x00", "")

    # Strip directory separators to prevent path traversal
    name = name.replace("/", "").replace("\\", "")

    # Strip leading/trailing whitespace and dots
    name = name.strip().strip(".")

    # Limit to maximum filename length
    name = name[:_MAX_FILENAME_LENGTH]

    return name


def validate_file_extension(filename: str) -> str:
    """Validate that *filename* has an allowed extension.

    Returns the lowercase extension (without the dot) on success.
    Raises ``ValidationException`` with ``INVALID_FILE_TYPE`` if the
    extension is missing or not in ``ALLOWED_FILE_EXTENSIONS``.
    """
    if "." not in filename:
        raise ValidationException(
            detail=f"File '{filename}' has no extension",
            error_code=INVALID_FILE_TYPE,
            fields=["file"],
        )

    extension = filename.rsplit(".", maxsplit=1)[-1].lower()

    if extension not in ALLOWED_FILE_EXTENSIONS:
        raise ValidationException(
            detail=f"File extension '.{extension}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}",
            error_code=INVALID_FILE_TYPE,
            fields=["file"],
        )

    return extension


def validate_uuid(value: str) -> str:
    """Validate that *value* is a well-formed UUID string.

    Returns the original string on success.
    Raises ``ValidationException`` with ``INVALID_UUID_FORMAT`` if the
    value cannot be parsed as a UUID.
    """
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise ValidationException(
            detail=f"Invalid UUID format: '{value}'",
            error_code=INVALID_UUID_FORMAT,
            fields=["id"],
        )

    return value
