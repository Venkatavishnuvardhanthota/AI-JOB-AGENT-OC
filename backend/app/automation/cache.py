from __future__ import annotations

import time
from threading import Lock
from typing import Any

from app.automation.config import AutomationConfig


class AutomationCache:
    def __init__(self, config: AutomationConfig) -> None:
        self._cache: dict[str, tuple[float, Any]] = {}
        self._ttl = config.cache_ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            timestamp, value = entry
            if time.monotonic() - timestamp >= self._ttl:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = (time.monotonic(), value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
