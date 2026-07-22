from __future__ import annotations

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.orchestration.health_manager import ProviderHealthManager
from app.jobs.registry import JobProviderRegistry
from app.jobs.schemas import JobSearchRequest

logger = structlog.get_logger(__name__)

STARTUP_PROVIDERS = frozenset({"wellfound", "y_combinator"})
ATS_PROVIDERS = frozenset({"greenhouse", "lever", "ashby", "workday", "smartrecruiters", "bamboohr", "recruitee"})


class ProviderSelector:
    def __init__(
        self,
        registry: JobProviderRegistry,
        config: JobDiscoveryConfig,
        health_manager: ProviderHealthManager | None = None,
    ) -> None:
        self._registry = registry
        self._config = config
        self._health = health_manager

    def select(self, request: JobSearchRequest) -> list[str]:
        candidates = self._get_candidates(request)
        return self._filter(request, candidates)

    def _get_candidates(self, request: JobSearchRequest) -> list[str]:
        if request.providers:
            return [p for p in request.providers if self._registry.is_registered(p)]

        registered = self._registry.list_providers()
        enabled = self._config.enabled_providers
        if enabled:
            return [p for p in registered if p in enabled]
        return registered

    def _filter(self, request: JobSearchRequest, candidates: list[str]) -> list[str]:
        result: list[str] = []

        for name in candidates:
            if name == "mock":
                result.append(name)
                continue

            if self._health and not self._health.is_healthy(name):
                logger.info("Skipping unhealthy provider", provider=name)
                continue

            if request.remote_only and not self._supports_remote(name):
                continue

            if request.employment_type and not self._supports_employment_filter(name):
                continue

            result.append(name)

        if self._health:
            deprioritized = [p for p in result if self._health.is_deprioritized(p)]
            healthy = [p for p in result if p not in deprioritized]
            result = healthy + deprioritized

        return result

    def _supports_remote(self, name: str) -> bool:
        provider = self._registry.resolve(name)
        return provider.supports_filters

    def _supports_employment_filter(self, name: str) -> bool:
        provider = self._registry.resolve(name)
        return provider.supports_filters

    @staticmethod
    def is_startup_provider(name: str) -> bool:
        return name in STARTUP_PROVIDERS

    @staticmethod
    def is_ats_provider(name: str) -> bool:
        return name in ATS_PROVIDERS
