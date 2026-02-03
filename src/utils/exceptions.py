"""
Centralized exception handling for Sports Card AI Agent
"""


class SportsCardException(Exception):
    """Base exception for application"""

    pass


class ConfigurationError(SportsCardException):
    """Raised when configuration is missing or invalid"""

    pass


class APIKeyMissingError(ConfigurationError):
    """Raised when required API key is missing"""

    pass


class DatabaseError(SportsCardException):
    """Raised when database operation fails"""

    pass


class ExternalAPIError(SportsCardException):
    """Raised when external API call fails"""

    pass
