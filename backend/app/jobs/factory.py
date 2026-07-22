from __future__ import annotations

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.registry import JobProviderRegistry

logger = structlog.get_logger(__name__)


class JobProviderFactory:
    def __init__(self, registry: JobProviderRegistry, config: JobDiscoveryConfig) -> None:
        self._registry = registry
        self._config = config

    def register_all(self) -> None:
        from app.jobs.providers.adzuna import AdzunaJobProvider
        from app.jobs.providers.mock import MockJobProvider

        registrations: list[tuple[str, type]] = [
            ("mock", MockJobProvider),
        ]

        enabled = self._config.enabled_providers
        if "adzuna" in enabled and self._config.adzuna.app_id and self._config.adzuna.api_key:
            registrations.append(("adzuna", AdzunaJobProvider))

        for name, provider_class in registrations:
            if not self._registry.is_registered(name):
                provider = provider_class(self._config)
                self._registry.register(provider)
                logger.info("Registered job provider", name=name)
