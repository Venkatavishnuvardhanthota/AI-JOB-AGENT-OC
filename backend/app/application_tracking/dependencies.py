from __future__ import annotations

from functools import lru_cache

from app.application_tracking.config import ApplicationTrackingConfig
from app.application_tracking.service import ApplicationTrackingService


@lru_cache
def _get_config() -> ApplicationTrackingConfig:
    return ApplicationTrackingConfig()


@lru_cache
def get_application_tracking_service() -> ApplicationTrackingService:
    return ApplicationTrackingService(config=_get_config())
