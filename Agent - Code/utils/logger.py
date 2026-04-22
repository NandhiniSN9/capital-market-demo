"""Centralised logger — human-readable for dev, structured JSON for production."""

import logging
import sys

from settings import get_settings

_GREY = "\033[90m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

_LEVEL_COLOURS = {
    "DEBUG": _GREY, "INFO": _GREEN, "WARNING": _YELLOW,
    "ERROR": _RED, "CRITICAL": _RED + _BOLD,
}


class _PrettyFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        colour = _LEVEL_COLOURS.get(level, _RESET)
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        location = f"{record.filename}:{record.lineno}"
        message = record.getMessage()
        _std = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        extras = {k: v for k, v in record.__dict__.items() if k not in _std}
        extra_str = "  |  " + "  ".join(f"{k}={v}" for k, v in extras.items()) if extras else ""
        line = (
            f"{_GREY}{timestamp}{_RESET}  "
            f"{colour}{level:<8}{_RESET}  "
            f"{_CYAN}{location:<30}{_RESET}  "
            f"{message}{_GREY}{extra_str}{_RESET}"
        )
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json
        _std = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        payload: dict = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "file": f"{record.filename}:{record.lineno}",
            "msg": record.getMessage(),
        }
        payload.update({k: v for k, v in record.__dict__.items() if k not in _std})
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def _build_logger() -> logging.Logger:
    log = logging.getLogger("unified_agent")
    if log.handlers:
        return log
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log.setLevel(level)
    log.propagate = False
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.terminator = "\n"
    if settings.app_env == "production":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(_PrettyFormatter())
    log.addHandler(handler)
    for noisy in ("httpx", "databricks", "openai", "urllib3", "langchain", "langgraph"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    return log


logger = _build_logger()
