import time
from threading import Lock
from typing import Any


class TTLCache:
    """Simple thread-safe in-memory TTL cache."""

    def __init__(self, default_ttl_seconds: int = 300) -> None:
        self._default_ttl = default_ttl_seconds
        self._store: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            expiry = self._expiry.get(key)
            if expiry is None:
                return None
            if time.monotonic() > expiry:
                self._store.pop(key, None)
                self._expiry.pop(key, None)
                return None
            return self._store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self._default_ttl
        with self._lock:
            self._store[key] = value
            self._expiry[key] = time.monotonic() + ttl

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._expiry.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._expiry.clear()

    def invalidate_by_prefix(self, prefix: str) -> None:
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                self._store.pop(k, None)
                self._expiry.pop(k, None)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)


_job_cache: TTLCache | None = None


def get_job_cache() -> TTLCache:
    global _job_cache
    if _job_cache is None:
        _job_cache = TTLCache(default_ttl_seconds=300)
    return _job_cache
