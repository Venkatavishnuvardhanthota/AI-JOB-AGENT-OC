from __future__ import annotations

import time
from threading import Lock

from app.job_matching.config import MatchingConfig
from app.job_matching.schemas import MatchResult


class MatchCache:
    def __init__(self, config: MatchingConfig) -> None:
        self._cache: dict[str, tuple[float, MatchResult]] = {}
        self._ttl = config.cache_ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> MatchResult | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            timestamp, result = entry
            if time.monotonic() - timestamp >= self._ttl:
                del self._cache[key]
                return None
            return result

    def set(self, key: str, result: MatchResult) -> None:
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
        job_id: str | None,
        job_skills_hash: str | None = None,
    ) -> str:
        parts = [str(profile_hash or ""), str(job_id or "")]
        if job_skills_hash:
            parts.append(job_skills_hash)
        return ":".join(parts)
