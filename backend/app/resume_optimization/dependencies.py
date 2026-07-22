from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.resume_optimization.config import OptimizationConfig
from app.resume_optimization.service import ResumeOptimizationService


@lru_cache
def _get_config() -> OptimizationConfig:
    return OptimizationConfig(
        cache_ttl_seconds=getattr(settings, "RESUME_OPTIMIZATION_CACHE_TTL", 300),
    )


@lru_cache
def get_resume_optimization_service() -> ResumeOptimizationService:
    return ResumeOptimizationService(config=_get_config())
