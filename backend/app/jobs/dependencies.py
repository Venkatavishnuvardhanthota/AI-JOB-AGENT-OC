from __future__ import annotations

from functools import lru_cache

from app.jobs.config import (
    AdzunaConfig,
    AshbyConfig,
    GreenhouseConfig,
    JobDiscoveryConfig,
    LeverConfig,
    WellfoundConfig,
    YCombinatorConfig,
)
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
        wellfound=WellfoundConfig(
            base_url=settings.WELLFOUND_BASE_URL,
            page_size=settings.WELLFOUND_PAGE_SIZE,
            rate_limit_rate=settings.WELLFOUND_RATE_LIMIT_RATE,
            rate_limit_burst=settings.WELLFOUND_RATE_LIMIT_BURST,
        ),
        y_combinator=YCombinatorConfig(
            base_url=settings.Y_COMBINATOR_BASE_URL,
            page_size=settings.Y_COMBINATOR_PAGE_SIZE,
            rate_limit_rate=settings.Y_COMBINATOR_RATE_LIMIT_RATE,
            rate_limit_burst=settings.Y_COMBINATOR_RATE_LIMIT_BURST,
        ),
        greenhouse=GreenhouseConfig(
            base_url=settings.GREENHOUSE_BASE_URL,
            page_size=settings.GREENHOUSE_PAGE_SIZE,
            rate_limit_rate=settings.GREENHOUSE_RATE_LIMIT_RATE,
            rate_limit_burst=settings.GREENHOUSE_RATE_LIMIT_BURST,
        ),
        lever=LeverConfig(
            base_url=settings.LEVER_BASE_URL,
            page_size=settings.LEVER_PAGE_SIZE,
            rate_limit_rate=settings.LEVER_RATE_LIMIT_RATE,
            rate_limit_burst=settings.LEVER_RATE_LIMIT_BURST,
        ),
        ashby=AshbyConfig(
            base_url=settings.ASHBY_BASE_URL,
            page_size=settings.ASHBY_PAGE_SIZE,
            rate_limit_rate=settings.ASHBY_RATE_LIMIT_RATE,
            rate_limit_burst=settings.ASHBY_RATE_LIMIT_BURST,
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
