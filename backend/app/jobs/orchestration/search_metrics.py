from __future__ import annotations

from threading import Lock

import structlog

logger = structlog.get_logger(__name__)


class SearchMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._search_count: int = 0
        self._total_duration_ms: float = 0.0
        self._provider_latency: dict[str, list[float]] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._jobs_before_dedup: int = 0
        self._jobs_after_dedup: int = 0
        self._provider_failures: dict[str, int] = {}
        self._providers_queried: dict[str, int] = {}

    def record_search(
        self,
        duration_ms: float,
        provider_latencies: dict[str, float],
        cache_hit: bool,
        jobs_before_dedup: int,
        jobs_after_dedup: int,
        provider_failures: list[str],
        providers_queried: list[str],
    ) -> None:
        with self._lock:
            self._search_count += 1
            self._total_duration_ms += duration_ms

            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

            self._jobs_before_dedup += jobs_before_dedup
            self._jobs_after_dedup += jobs_after_dedup

            for provider, lat in provider_latencies.items():
                if provider not in self._provider_latency:
                    self._provider_latency[provider] = []
                self._provider_latency[provider].append(lat)

            for provider in provider_failures:
                self._provider_failures[provider] = self._provider_failures.get(provider, 0) + 1

            for provider in providers_queried:
                self._providers_queried[provider] = self._providers_queried.get(provider, 0) + 1

    def summary(self) -> dict:
        with self._lock:
            avg_duration = self._total_duration_ms / self._search_count if self._search_count > 0 else 0.0

            provider_stats: dict = {}
            for provider, lats in self._provider_latency.items():
                provider_stats[provider] = {
                    "avg_latency_ms": round(sum(lats) / len(lats), 1) if lats else 0.0,
                    "calls": len(lats),
                    "failures": self._provider_failures.get(provider, 0),
                }
            for provider, count in self._provider_failures.items():
                if provider not in provider_stats:
                    provider_stats[provider] = {
                        "avg_latency_ms": 0.0,
                        "calls": 0,
                        "failures": count,
                    }

            total_before = self._jobs_before_dedup
            total_after = self._jobs_after_dedup

            return {
                "total_searches": self._search_count,
                "avg_duration_ms": round(avg_duration, 1),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_ratio": (
                    self._cache_hits / (self._cache_hits + self._cache_misses)
                    if (self._cache_hits + self._cache_misses) > 0
                    else 0.0
                ),
                "total_jobs_before_dedup": total_before,
                "total_jobs_after_dedup": total_after,
                "total_duplicates_removed": total_before - total_after if total_before >= total_after else 0,
                "provider_stats": provider_stats,
            }

    def reset(self) -> None:
        with self._lock:
            self._search_count = 0
            self._total_duration_ms = 0.0
            self._provider_latency.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self._jobs_before_dedup = 0
            self._jobs_after_dedup = 0
            self._provider_failures.clear()
            self._providers_queried.clear()
