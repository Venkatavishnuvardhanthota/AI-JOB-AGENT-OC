from __future__ import annotations

from functools import lru_cache

from app.jobs.config import AdzunaConfig, JobDiscoveryConfig
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
        request_timeout_seconds=settings.JOB_REQUEST_TIMEOUT_SECONDS,
        retry_count=settings.JOB_RETRY_COUNT,
        default_search_limit=settings.JOB_DEFAULT_SEARCH_LIMIT,
        adzuna=AdzunaConfig(
            app_id=settings.ADZUNA_APP_ID,
            api_key=settings.ADZUNA_API_KEY,
            base_url=settings.ADZUNA_BASE_URL,
            page_size=settings.ADZUNA_PAGE_SIZE,
            rate_limit_rate=settings.ADZUNA_RATE_LIMIT_RATE,
            rate_limit_burst=settings.ADZUNA_RATE_LIMIT_BURST,
        ),
    )


def get_registry() -> JobProviderRegistry:
    return _get_registry()


def get_job_discovery_config() -> JobDiscoveryConfig:
    return _get_config()


def ensure_providers_registered() -> None:
    registry = _get_registry()
    if registry.count() == 0:
        from app.jobs.factory import JobProviderFactory

        config = _get_config()
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        import structlog

        logger = structlog.get_logger(__name__)
        logger.info("Registered default job providers")


def get_job_discovery_service() -> JobDiscoveryService:
    registry = _get_registry()
    config = _get_config()
    ensure_providers_registered()
    return JobDiscoveryService(registry=registry, config=config)
