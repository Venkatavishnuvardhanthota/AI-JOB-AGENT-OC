from __future__ import annotations

from typing import Any

import structlog

from app.uploads.config import UploadsConfig
from app.uploads.providers.base import BaseUploadProvider
from app.uploads.registry import UploadProviderRegistry

logger = structlog.get_logger(__name__)


class UploadProviderFactory:
    def __init__(
        self,
        registry: UploadProviderRegistry,
        config: UploadsConfig | None = None,
    ) -> None:
        self._registry = registry
        self._config = config or UploadsConfig()
        self._logger = logger.bind(service="upload_factory")

    def create_provider(self, name: str) -> Any:
        provider = BaseUploadProvider(name=name)
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
