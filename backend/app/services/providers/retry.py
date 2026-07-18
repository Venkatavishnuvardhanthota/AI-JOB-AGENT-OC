import asyncio
import logging
from collections.abc import Awaitable, Callable
from functools import wraps

from app.services.providers.errors import (
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


async def retry_async(
    fn: Callable[..., Awaitable],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
    provider: str | None = None,
    *args,
    **kwargs,
):
    """Execute an async callable with exponential backoff retry."""
    if retryable_exceptions is None:
        retryable_exceptions = (
            ProviderRateLimitError, ProviderTimeoutError,
            ProviderUnavailableError, TimeoutError, ConnectionError,
        )

    last_exception: Exception | None = None
    delay = base_delay

    for attempt in range(max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            if isinstance(e, ProviderRateLimitError) and e.retry_after:
                delay = min(e.retry_after, max_delay)
            if attempt < max_retries:
                logger.warning(
                    "Retry attempt %d/%d for %s after %.2fs: %s",
                    attempt + 1, max_retries, provider or "unknown", delay, e,
                )
                await asyncio.sleep(delay)
                delay = min(delay * backoff, max_delay)
        except ProviderError:
            raise

    msg = f"All {max_retries + 1} retries exhausted for {provider or 'unknown'}"
    raise ProviderUnavailableError(msg, provider=provider) from last_exception


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff: float = 2.0,
):
    """Decorator for async functions needing retry logic."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            provider = getattr(fn, "__qualname__", None)
            return await retry_async(
                fn, max_retries, base_delay, max_delay, backoff,
                None, provider,
                *args,
                **kwargs,
            )
        return wrapper
    return decorator
