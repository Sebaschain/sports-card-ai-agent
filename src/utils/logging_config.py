"""
Centralized logging configuration with structured JSON logging support.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from src.utils.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "context_id"):
            log_data["context_id"] = record.context_id
        if hasattr(record, "search_query"):
            log_data["search_query"] = record.search_query
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "cached"):
            log_data["cached"] = record.cached
        if hasattr(record, "error"):
            log_data["error"] = record.error

        # Add extra dict if present
        if record.__dict__.get("extra"):
            for key, value in record.extra.items():
                if key not in log_data:
                    log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(use_json: bool = True) -> None:
    """
    Setup application logging configuration.

    Args:
        use_json: If True, use JSON formatting for structured logging.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure format
    if use_json:
        log_format = JSONFormatter()
    else:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure handlers
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(self.__class__.__name__)

    def _log_with_context(
        self,
        level: int,
        message: str,
        context: dict[str, Any] | None = None,
        exc_info: bool = False,
    ) -> None:
        """
        Log a message with optional context.

        Args:
            level: Logging level (logging.INFO, logging.ERROR, etc.)
            message: Message to log
            context: Optional context dictionary
            exc_info: If True, include exception info
        """
        extra = {"extra": context} if context else {}
        self.logger.log(level, message, exc_info=exc_info, extra=extra)
