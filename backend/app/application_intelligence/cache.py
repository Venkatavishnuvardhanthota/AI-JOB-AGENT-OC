from __future__ import annotations

import time
from threading import Lock

from app.application_intelligence.config import ApplicationIntelligenceConfig
from app.application_intelligence.schemas import ApplicationIntelligence


class AnalysisCache:
    def __init__(self, config: ApplicationIntelligenceConfig) -> None:
        self._cache: dict[str, tuple[float, ApplicationIntelligence]] = {}
        self._ttl = config.cache_ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> ApplicationIntelligence | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            timestamp, result = entry
            if time.monotonic() - timestamp >= self._ttl:
                del self._cache[key]
                return None
            return result

    def set(self, key: str, result: ApplicationIntelligence) -> None:
        with self._lock:
            self._cache[key] = (time.monotonic(), result)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def compute_key(self, job_hash: str, profile_hash: str | None = None) -> str:
        return f"{profile_hash or ''}:{job_hash}"
