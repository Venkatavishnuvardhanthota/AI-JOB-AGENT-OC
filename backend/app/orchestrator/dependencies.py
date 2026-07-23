from __future__ import annotations

from functools import lru_cache

from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.service import OrchestratorService


@lru_cache
def get_orchestrator_config() -> OrchestratorConfig:
    return OrchestratorConfig()


@lru_cache
def get_orchestrator_service() -> OrchestratorService:
    return OrchestratorService(config=get_orchestrator_config())
