from __future__ import annotations

import time
from threading import Lock

from app.review.config import ReviewConfig
from app.review.schemas import ReviewRecord


class ReviewCache:
    def __init__(self, config: ReviewConfig) -> None:
        self._cache: dict[str, tuple[float, ReviewRecord]] = {}
        self._ttl = config.cache_ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> ReviewRecord | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            timestamp, result = entry
            if time.monotonic() - timestamp >= self._ttl:
                del self._cache[key]
                return None
            return result

    def set(self, key: str, record: ReviewRecord) -> None:
        with self._lock:
            self._cache[key] = (time.monotonic(), record)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
