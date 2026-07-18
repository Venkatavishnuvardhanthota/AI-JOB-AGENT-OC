"""Simple metrics counters for provider operations."""

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class ProviderMetrics:
    """Per-provider metrics snapshot."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_count: int = 0
    timeout_count: int = 0
    parse_error_count: int = 0
    total_jobs_found: int = 0
    total_search_time_ms: float = 0.0
    last_request_time: float | None = None
    last_error: str | None = None


class MetricsCollector:
    """Thread-safe metrics collector for provider operations."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._metrics: dict[str, ProviderMetrics] = defaultdict(ProviderMetrics)

    def record_request(self, provider: str, success: bool, duration_ms: float) -> None:
        with self._lock:
            m = self._metrics[provider]
            m.total_requests += 1
            m.last_request_time = time.time()
            if success:
                m.successful_requests += 1
            else:
                m.failed_requests += 1

    def record_rate_limit(self, provider: str) -> None:
        with self._lock:
            self._metrics[provider].rate_limited_count += 1

    def record_timeout(self, provider: str) -> None:
        with self._lock:
            self._metrics[provider].timeout_count += 1

    def record_parse_error(self, provider: str) -> None:
        with self._lock:
            self._metrics[provider].parse_error_count += 1

    def record_jobs_found(self, provider: str, count: int) -> None:
        with self._lock:
            self._metrics[provider].total_jobs_found += count

    def record_search_time(self, provider: str, duration_ms: float) -> None:
        with self._lock:
            self._metrics[provider].total_search_time_ms += duration_ms

    def record_error(self, provider: str, error: str) -> None:
        with self._lock:
            self._metrics[provider].last_error = error

    def get_metrics(self, provider: str | None = None) -> dict[str, ProviderMetrics]:
        with self._lock:
            if provider:
                return {provider: self._metrics.get(provider, ProviderMetrics())}
            return dict(self._metrics)

    def reset(self, provider: str | None = None) -> None:
        with self._lock:
            if provider:
                self._metrics[provider] = ProviderMetrics()
            else:
                self._metrics.clear()

    def summary(self) -> dict[str, Any]:
        """Return a JSON-serializable summary of all metrics."""
        with self._lock:
            return {
                name: {
                    "total_requests": m.total_requests,
                    "successful_requests": m.successful_requests,
                    "failed_requests": m.failed_requests,
                    "rate_limited_count": m.rate_limited_count,
                    "timeout_count": m.timeout_count,
                    "parse_error_count": m.parse_error_count,
                    "total_jobs_found": m.total_jobs_found,
                    "avg_search_time_ms": (
                        round(m.total_search_time_ms / m.total_requests, 1)
                        if m.total_requests > 0 else 0.0
                    ),
                    "last_error": m.last_error,
                }
                for name, m in self._metrics.items()
            }


_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
