from __future__ import annotations

from functools import lru_cache

from app.operations.config import OperationsConfig
from app.operations.service import OperationsService


@lru_cache
def get_operations_config() -> OperationsConfig:
    return OperationsConfig()


@lru_cache
def get_operations_service() -> OperationsService:
    return OperationsService(config=get_operations_config())
