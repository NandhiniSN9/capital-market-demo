"""Centralized logging configuration."""

import logging
import sys
import json
import logging
import sys
import traceback

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger_name": record.name,
            "filename": record.filename,
            "line_number": record.lineno,
            "message": record.getMessage(),
        }

        # Capture exception information when present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stacktrace": traceback.format_exception(*record.exc_info),
            }

        # Support custom fields passed via the extra dict
        for field in ("trace_id", "chat_id", "document_id", "session_id"):
            value = getattr(record, field, None)
            if value is not None:
                log_entry[field] = value

        return json.dumps(log_entry, default=str)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with plain text output.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    _logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when called multiple times
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        _logger.addHandler(handler)

    # Import here to avoid circular dependency at module level
    try:
        from BE.settings import get_settings

        _logger.setLevel(get_settings().log_level.upper())
    except Exception:
        _logger.setLevel(logging.INFO)

    return _logger


# Reduce noise from third-party libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("databricks").setLevel(logging.WARNING)

def setup_logger(name: str = "rfq_dashboard", level: int = logging.INFO) -> logging.Logger:
    """Create and configure a logger instance."""
    _logger = logging.getLogger(name)
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        _logger.addHandler(handler)
        _logger.setLevel(level)
    return _logger


logger = setup_logger()
