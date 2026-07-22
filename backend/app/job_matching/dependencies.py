from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.job_matching.config import MatchingConfig
from app.job_matching.service import JobMatchingService


@lru_cache
def _get_config() -> MatchingConfig:
    return MatchingConfig(
        cache_ttl_seconds=getattr(settings, "JOB_MATCHING_CACHE_TTL", 300),
    )


@lru_cache
def get_job_matching_service() -> JobMatchingService:
    return JobMatchingService(config=_get_config())
