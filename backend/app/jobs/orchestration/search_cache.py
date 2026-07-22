from __future__ import annotations

import hashlib
import json
import time
from threading import Lock

import structlog

from app.jobs.schemas import JobSearchRequest, JobSearchResponse

logger = structlog.get_logger(__name__)


class SearchCache:
    def __init__(self, ttl_seconds: int = 300, max_size: int = 500) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._cache: dict[str, tuple[float, JobSearchResponse]] = {}
        self._stats: dict[str, int] = {"hits": 0, "misses": 0}
        self._lock = Lock()

    def _make_key(self, request: JobSearchRequest) -> str:
        parts = {
            "q": request.query or "",
            "kw": " ".join(sorted(request.keywords)) if request.keywords else "",
            "loc": request.location or "",
            "remote": str(request.remote_only or ""),
            "et": request.employment_type.value if request.employment_type else "",
            "el": request.experience_level.value if request.experience_level else "",
            "smin": str(request.salary_min or ""),
            "smax": str(request.salary_max or ""),
            "prov": " ".join(sorted(request.providers)) if request.providers else "",
            "dedup": str(request.deduplicate),
            "within": str(request.posted_within_days or ""),
            "limit": str(request.limit),
        }
        raw = json.dumps(parts, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, request: JobSearchRequest) -> JobSearchResponse | None:
        key = self._make_key(request)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            timestamp, response = entry
            if time.monotonic() - timestamp >= self._ttl:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return response

    def set(self, request: JobSearchRequest, response: JobSearchResponse) -> None:
        if response.metadata.total_results == 0:
            return

        key = self._make_key(request)
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_oldest()
            self._cache[key] = (time.monotonic(), response)

    def invalidate(self, provider_name: str | None = None) -> int:
        with self._lock:
            if provider_name is None:
                count = len(self._cache)
                self._cache.clear()
                return count

            keys_to_delete: list[str] = []
            for key, (_, response) in self._cache.items():
                if provider_name in response.metadata.providers_queried:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]

            return len(keys_to_delete)

    def _evict_oldest(self) -> None:
        oldest_key: str | None = None
        oldest_ts: float = float("inf")
        for key, (ts, _) in self._cache.items():
            if ts < oldest_ts:
                oldest_ts = ts
                oldest_key = key
        if oldest_key is not None:
            del self._cache[oldest_key]

    def stats(self) -> dict:
        with self._lock:
            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "size": len(self._cache),
                "max_size": self._max_size,
                "ttl_seconds": self._ttl,
                "hit_ratio": (
                    self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                    if (self._stats["hits"] + self._stats["misses"]) > 0
                    else 0.0
                ),
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._stats = {"hits": 0, "misses": 0}
