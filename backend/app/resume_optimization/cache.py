from __future__ import annotations

import time
from threading import Lock

from app.resume_optimization.config import OptimizationConfig
from app.resume_optimization.schemas import OptimizedResume


class OptimizationCache:
    def __init__(self, config: OptimizationConfig) -> None:
        self._cache: dict[str, tuple[float, OptimizedResume]] = {}
        self._ttl = config.cache_ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> OptimizedResume | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            timestamp, result = entry
            if time.monotonic() - timestamp >= self._ttl:
                del self._cache[key]
                return None
            return result

    def set(self, key: str, result: OptimizedResume) -> None:
        with self._lock:
            self._cache[key] = (time.monotonic(), result)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def compute_key(
        self,
        profile_hash: str | None,
        job_hash: str | None,
        resume_hash: str | None = None,
    ) -> str:
        parts = [str(profile_hash or ""), str(job_hash or "")]
        if resume_hash:
            parts.append(resume_hash)
        return ":".join(parts)
