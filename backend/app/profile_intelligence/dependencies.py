from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.profile_intelligence.service import ProfileIntelligenceService


@lru_cache
def _get_cache_ttl() -> int:
    return getattr(settings, "PROFILE_INTELLIGENCE_CACHE_TTL", 300)


def get_profile_intelligence_service(
    session,
    cache_ttl: int | None = None,
) -> ProfileIntelligenceService:
    return ProfileIntelligenceService(
        session=session,
        cache_ttl_seconds=cache_ttl or _get_cache_ttl(),
    )
