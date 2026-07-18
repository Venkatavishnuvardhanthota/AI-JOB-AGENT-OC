"""Provider-specific structured logging utility."""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ProviderLogger:
    """Structured logger for provider operations.

    Wraps structlog with provider-specific context.
    """

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        self._log = logger.bind(provider=provider_name)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log.info(event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log.warning(event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log.error(event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log.debug(event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        self._log.exception(event, **kwargs)

    def request_summary(
        self,
        method: str,
        url: str,
        status_code: int,
        duration_ms: float,
        **kwargs: Any,
    ) -> None:
        self._log.info(
            "provider_request",
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=round(duration_ms, 1),
            **kwargs,
        )

    def search_summary(
        self,
        query: str,
        results_count: int,
        duration_ms: float,
        error: str | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {
            "event": "provider_search",
            "query": query,
            "results_count": results_count,
            "duration_ms": round(duration_ms, 1),
        }
        if error:
            kwargs["error"] = error
            self._log.warning(**kwargs)
        else:
            self._log.info(**kwargs)
