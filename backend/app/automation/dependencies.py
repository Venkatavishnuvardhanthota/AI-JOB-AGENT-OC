from __future__ import annotations

from functools import lru_cache

from app.automation.config import AutomationConfig
from app.automation.service import AutomationService


@lru_cache
def _get_config() -> AutomationConfig:
    return AutomationConfig()


@lru_cache
def get_automation_service() -> AutomationService:
    return AutomationService(config=_get_config())
