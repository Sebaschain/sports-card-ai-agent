"""
Project configuration
Load environment variables and global settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variables"""
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, default)


class Settings:
    """Global application configuration"""

    # OpenAI
    OPENAI_API_KEY: str = get_secret("OPENAI_API_KEY", "")

    # eBay API
    EBAY_APP_ID: str = get_secret("EBAY_APP_ID", "")
    EBAY_CERT_ID: str = get_secret("EBAY_CERT_ID", "")
    EBAY_DEV_ID: str = get_secret("EBAY_DEV_ID", "")
    EBAY_TOKEN: str = get_secret("EBAY_TOKEN", "")

    # Ball Don't Lie
    BDL_API_KEY: str = get_secret("BDL_API_KEY", "")

    # Database
    DATABASE_URL: str = get_secret("DATABASE_URL", "sqlite:///./data/sports_cards.db")

    # Logging
    LOG_LEVEL: str = get_secret("LOG_LEVEL", "INFO")

    # Project
    PROJECT_NAME: str = "Sports Card AI Agent"
    VERSION: str = "1.0.0"


def validate_configuration():
    """Validate critical configuration settings"""
    import logging

    errors = []
    warnings = []

    # Check required API keys
    if not settings.EBAY_APP_ID:
        warnings.append(
            "EBAY_APP_ID not configured - eBay features will use simulated data"
        )

    if not settings.OPENAI_API_KEY:
        warnings.append("OPENAI_API_KEY not configured - AI features will be limited")

    # Check database configuration
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")

    # Log results
    logger = logging.getLogger(__name__)

    if warnings:
        for warning in warnings:
            logger.warning(f"Configuration Warning: {warning}")

    if errors:
        for error in errors:
            logger.error(f"Configuration Error: {error}")
        raise Exception(f"Configuration errors: {'; '.join(errors)}")

    return True


# Global configuration instance
settings = Settings()
