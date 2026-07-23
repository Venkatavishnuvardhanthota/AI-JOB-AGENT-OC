from __future__ import annotations

from functools import lru_cache

from app.workflow.config import WorkflowConfig
from app.workflow.service import WorkflowService


@lru_cache
def _get_config() -> WorkflowConfig:
    return WorkflowConfig()


@lru_cache
def get_workflow_service() -> WorkflowService:
    return WorkflowService(config=_get_config())
