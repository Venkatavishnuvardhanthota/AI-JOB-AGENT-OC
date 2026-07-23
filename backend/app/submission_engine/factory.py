from __future__ import annotations

from typing import Any

import structlog

from app.submission_engine.config import SubmissionEngineConfig
from app.submission_engine.providers.base import BaseSubmissionProvider
from app.submission_engine.registry import SubmissionProviderRegistry

logger = structlog.get_logger(__name__)


class SubmissionProviderFactory:
    def __init__(
        self,
        registry: SubmissionProviderRegistry,
        config: SubmissionEngineConfig | None = None,
    ) -> None:
        self._registry = registry
        self._config = config or SubmissionEngineConfig()
        self._logger = logger.bind(service="submission_factory")

    def create_provider(self, name: str) -> Any:
        provider = BaseSubmissionProvider(name=name)
        self._registry.register(name, provider)
        return provider

    def register_all(self) -> None:
        names = ["greenhouse", "lever", "ashby", "workday", "smartrecruiters", "bamboohr", "recruitee"]
        for name in names:
            if not self._registry.is_registered(name):
                self.create_provider(name)

    def detect_provider(self, url: str) -> Any | None:
        for name in self._registry.list_providers():
            provider = self._registry.resolve(name)
            if hasattr(provider, "supports") and provider.supports(url):
                return provider
        return None
