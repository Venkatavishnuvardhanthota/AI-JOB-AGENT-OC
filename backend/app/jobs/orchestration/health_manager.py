from __future__ import annotations

import time
from collections import deque
from threading import RLock

import structlog

logger = structlog.get_logger(__name__)


class ProviderHealthManager:
    def __init__(
        self,
        window_seconds: int = 300,
        failure_threshold: float = 0.5,
        min_samples: int = 5,
        cooldown_seconds: int = 60,
        latency_threshold_ms: float = 10000.0,
    ) -> None:
        self._window_seconds = window_seconds
        self._failure_threshold = failure_threshold
        self._min_samples = min_samples
        self._cooldown_seconds = cooldown_seconds
        self._latency_threshold_ms = latency_threshold_ms

        self._records: dict[str, deque[dict]] = {}
        self._deprioritized_until: dict[str, float] = {}
        self._lock = RLock()

    def record_success(self, provider: str, latency_ms: float = 0.0) -> None:
        with self._lock:
            self._add_record(provider, {"type": "success", "ts": time.monotonic(), "latency_ms": latency_ms})
            self._deprioritized_until.pop(provider, None)

    def record_failure(self, provider: str, latency_ms: float = 0.0) -> None:
        with self._lock:
            self._add_record(provider, {"type": "failure", "ts": time.monotonic(), "latency_ms": latency_ms})
            rate = self._failure_rate_locked(provider)
            if rate >= self._failure_threshold:
                until = time.monotonic() + self._cooldown_seconds
                self._deprioritized_until[provider] = until

    def is_healthy(self, provider: str) -> bool:
        with self._lock:
            until = self._deprioritized_until.get(provider, 0.0)
            if time.monotonic() < until:
                return False

            samples = self._records.get(provider)
            if not samples or len(samples) < self._min_samples:
                return True

            rate = self._failure_rate_locked(provider)
            if rate >= self._failure_threshold:
                return False

            avg_latency = self._avg_latency_locked(provider)
            return not avg_latency > self._latency_threshold_ms

    def is_deprioritized(self, provider: str) -> bool:
        with self._lock:
            until = self._deprioritized_until.get(provider, 0.0)
            return time.monotonic() < until

    def get_failure_rate(self, provider: str) -> float | None:
        with self._lock:
            samples = self._records.get(provider)
            if not samples or len(samples) < self._min_samples:
                return None
            return self._failure_rate_locked(provider)

    def get_avg_latency(self, provider: str) -> float | None:
        with self._lock:
            samples = self._records.get(provider)
            if not samples:
                return None
            return self._avg_latency_locked(provider)

    def summary(self) -> dict:
        with self._lock:
            result: dict = {}
            for provider in list(self._records.keys()):
                samples = self._records[provider]
                if not samples:
                    continue
                failures = sum(1 for s in samples if s["type"] == "failure")
                total = len(samples)
                avg_lat = sum(s["latency_ms"] for s in samples) / total if total > 0 else 0.0
                result[provider] = {
                    "total_samples": total,
                    "failures": failures,
                    "failure_rate": failures / total if total > 0 else 0.0,
                    "avg_latency_ms": round(avg_lat, 1),
                    "healthy": self.is_healthy(provider),
                }
            return result

    def _add_record(self, provider: str, record: dict) -> None:
        if provider not in self._records:
            self._records[provider] = deque(maxlen=100)
        self._records[provider].append(record)
        self._prune_old(provider)

    def _prune_old(self, provider: str) -> None:
        if provider not in self._records:
            return
        cutoff = time.monotonic() - self._window_seconds
        dq = self._records[provider]
        while dq and dq[0]["ts"] < cutoff:
            dq.popleft()

    def _failure_rate_locked(self, provider: str) -> float:
        self._prune_old(provider)
        samples = self._records.get(provider)
        if not samples or len(samples) < self._min_samples:
            return 0.0
        failures = sum(1 for s in samples if s["type"] == "failure")
        return failures / len(samples)

    def _avg_latency_locked(self, provider: str) -> float:
        samples = self._records.get(provider)
        if not samples:
            return 0.0
        return sum(s["latency_ms"] for s in samples) / len(samples)
