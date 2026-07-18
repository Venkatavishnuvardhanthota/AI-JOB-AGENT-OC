class ProviderError(Exception):
    """Base exception for all provider errors."""

    def __init__(self, message: str, provider: str | None = None) -> None:
        self.provider = provider
        super().__init__(message)


class ProviderAuthError(ProviderError):
    """Authentication/authorization failure from the provider."""

    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__(f"Auth error: {message}", provider=provider)


class ProviderRateLimitError(ProviderError):
    """Rate limited by the provider."""

    def __init__(self, message: str, provider: str | None = None, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limited: {message}", provider=provider)


class ProviderTimeoutError(ProviderError):
    """Request timed out connecting to the provider."""

    def __init__(self, message: str, provider: str | None = None, timeout: float | None = None) -> None:
        self.timeout = timeout
        super().__init__(f"Timeout: {message}", provider=provider)


class ProviderParseError(ProviderError):
    """Failed to parse the provider's response."""

    def __init__(self, message: str, provider: str | None = None, raw: str | None = None) -> None:
        self.raw = raw
        super().__init__(f"Parse error: {message}", provider=provider)


class ProviderUnavailableError(ProviderError):
    """Provider is temporarily unavailable."""

    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__(f"Unavailable: {message}", provider=provider)
