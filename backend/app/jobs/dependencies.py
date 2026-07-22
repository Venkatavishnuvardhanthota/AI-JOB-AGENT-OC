from __future__ import annotations

from functools import lru_cache

from app.jobs.config import JobDiscoveryConfig
from app.jobs.registry import JobProviderRegistry
from app.jobs.service import JobDiscoveryService


@lru_cache
def _get_registry() -> JobProviderRegistry:
    return JobProviderRegistry()


@lru_cache
def _get_config() -> JobDiscoveryConfig:
    from app.core.config import settings

    return JobDiscoveryConfig(
        enabled_providers=settings.ENABLED_JOB_PROVIDERS,
    )


def get_registry() -> JobProviderRegistry:
    return _get_registry()


def get_job_discovery_config() -> JobDiscoveryConfig:
    return _get_config()


def ensure_providers_registered() -> None:
    registry = _get_registry()
    if registry.count() == 0:
        from app.jobs.providers.mock import MockJobProvider

        config = _get_config()
        registry.register(MockJobProvider(config))
        import structlog

        logger = structlog.get_logger(__name__)
        logger.info("Registered default job providers")


def get_job_discovery_service() -> JobDiscoveryService:
    registry = _get_registry()
    config = _get_config()
    ensure_providers_registered()
    return JobDiscoveryService(registry=registry, config=config)
