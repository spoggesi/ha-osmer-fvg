"""Structured logging for OSMER FVG integration."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from .const import DOMAIN, VERSION

# Context variable for request IDs
_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class StructuredLogger:
    """Structured logger with consistent JSON output."""

    def __init__(self, name: str, level: int = logging.INFO) -> None:
        """Initialize structured logger."""
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._name = name

    def _get_context(self) -> dict[str, Any]:
        """Get base context for all logs."""
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "integration": DOMAIN,
            "version": VERSION,
            "logger": self._name,
        }

    def _add_request_id(self, context: dict[str, Any]) -> dict[str, Any]:
        """Add request ID if available."""
        request_id = _request_id_var.get()
        if request_id:
            context["request_id"] = request_id
        return context

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message with structure."""
        context = self._get_context()
        context["level"] = "DEBUG"
        context["message"] = msg
        context.update(kwargs)
        context = self._add_request_id(context)
        self._logger.debug(json.dumps(context, default=str))

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message with structure."""
        context = self._get_context()
        context["level"] = "INFO"
        context["message"] = msg
        context.update(kwargs)
        context = self._add_request_id(context)
        self._logger.info(json.dumps(context, default=str))

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message with structure."""
        context = self._get_context()
        context["level"] = "WARNING"
        context["message"] = msg
        context.update(kwargs)
        context = self._add_request_id(context)
        self._logger.warning(json.dumps(context, default=str))

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message with structure."""
        context = self._get_context()
        context["level"] = "ERROR"
        context["message"] = msg
        context.update(kwargs)
        context = self._add_request_id(context)
        self._logger.error(json.dumps(context, default=str))

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log exception with structure."""
        context = self._get_context()
        context["level"] = "ERROR"
        context["message"] = msg
        context["exception"] = True
        context.update(kwargs)
        context = self._add_request_id(context)
        self._logger.exception(json.dumps(context, default=str))


def get_request_id() -> str | None:
    """Get current request ID."""
    return _request_id_var.get()


def set_request_id(request_id: str | None = None) -> str:
    """Set current request ID and return it."""
    if request_id is None:
        import uuid

        request_id = str(uuid.uuid4())[:8]
    _request_id_var.set(request_id)
    return request_id


def reset_request_id() -> None:
    """Reset current request ID."""
    _request_id_var.set(None)


# Create logger instances
logger = StructuredLogger(__name__)
api_logger = StructuredLogger(f"{DOMAIN}.api")
coordinator_logger = StructuredLogger(f"{DOMAIN}.coordinator")
sensor_logger = StructuredLogger(f"{DOMAIN}.sensor")
weather_logger = StructuredLogger(f"{DOMAIN}.weather")
diagnostics_logger = StructuredLogger(f"{DOMAIN}.diagnostics")
