"""Custom exceptions for Sports Card AI Agent."""

from typing import Any


class SportsCardAIError(Exception):
    """Base exception for Sports Card AI Agent."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        self.message: str = message
        self.context: dict[str, Any] = context or {}
        super().__init__(self.message)


class MarketDataError(SportsCardAIError):
    """Exception raised when market data cannot be retrieved."""

    def __init__(self, message: str, data_source: str | None = None) -> None:
        self.data_source: str | None = data_source
        context: dict[str, Any] = {"data_source": data_source} if data_source else {}
        super().__init__(message, context)


class APITemporarilyUnavailableError(SportsCardAIError):
    """Exception raised when an API is temporarily unavailable."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        self.retry_after: float | None = retry_after
        context: dict[str, Any] = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, context)


class RateLimitExceededError(APITemporarilyUnavailableError):
    """Exception raised when API rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: float = 60.0) -> None:
        self.limit_type: str = "unknown"
        super().__init__(message, retry_after)

    def with_limit_type(self, limit_type: str) -> "RateLimitExceededError":
        """Add limit type information."""
        self.limit_type = limit_type
        self.context["limit_type"] = limit_type
        return self


class AuthenticationError(SportsCardAIError):
    """Exception raised when authentication fails."""

    def __init__(self, message: str, service: str | None = None) -> None:
        self.service: str | None = service
        context: dict[str, Any] = {"service": service} if service else {}
        super().__init__(message, context)


class ValidationError(SportsCardAIError):
    """Exception raised when validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
    ) -> None:
        self.field: str | None = field
        self.value: Any = value
        context: dict[str, Any] = {"field": field, "value": value} if field else {}
        super().__init__(message, context)


class ConfigurationError(SportsCardAIError):
    """Exception raised when there's a configuration issue."""

    def __init__(self, message: str, config_key: str | None = None) -> None:
        self.config_key: str | None = config_key
        context: dict[str, Any] = {"config_key": config_key} if config_key else {}
        super().__init__(message, context)
