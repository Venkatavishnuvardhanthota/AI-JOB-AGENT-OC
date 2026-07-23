from __future__ import annotations

import time
from threading import Lock

from app.application_package.config import PackageConfig
from app.application_package.schemas import ApplicationPackage


class PackageCache:
    def __init__(self, config: PackageConfig) -> None:
        self._cache: dict[str, tuple[float, ApplicationPackage]] = {}
        self._ttl = config.cache_ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> ApplicationPackage | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            timestamp, result = entry
            if time.monotonic() - timestamp >= self._ttl:
                del self._cache[key]
                return None
            return result

    def set(self, key: str, result: ApplicationPackage) -> None:
        with self._lock:
            self._cache[key] = (time.monotonic(), result)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @staticmethod
    def compute_key(
        profile_hash: str | None,
        job_hash: str | None,
        resume_hash: str | None = None,
        cover_letter_hash: str | None = None,
        match_hash: str | None = None,
    ) -> str:
        parts = [
            profile_hash or "",
            job_hash or "",
            resume_hash or "",
            cover_letter_hash or "",
            match_hash or "",
        ]
        return ":".join(parts)
