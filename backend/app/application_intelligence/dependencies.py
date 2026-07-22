from __future__ import annotations

from functools import lru_cache

from app.application_intelligence.config import ApplicationIntelligenceConfig
from app.application_intelligence.service import ApplicationIntelligenceService


@lru_cache
def _get_config() -> ApplicationIntelligenceConfig:
    return ApplicationIntelligenceConfig(
        cache_ttl_seconds=300,
    )


@lru_cache
def get_application_intelligence_service() -> ApplicationIntelligenceService:
    return ApplicationIntelligenceService(config=_get_config())
