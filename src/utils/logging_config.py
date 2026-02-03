"""
Centralized logging configuration
"""

import logging
import sys
from src.utils.config import settings


def setup_logging():
    """Setup application logging configuration"""

    # Configure logging level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(level=log_level, format=log_format, stream=sys.stdout)

    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(name)
