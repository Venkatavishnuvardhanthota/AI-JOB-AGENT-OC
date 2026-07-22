from __future__ import annotations

import threading

import structlog

from app.ai.exceptions import ConfigurationError, ProviderNotFoundError
from app.ai.interfaces import AIProvider
from app.ai.schemas import ProviderInfo

logger = structlog.get_logger(__name__)


class AIProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._lock = threading.Lock()

    def register(self, provider: AIProvider) -> None:
        with self._lock:
            if not provider.name:
                raise ConfigurationError("Provider must have a non-empty name.")
            if provider.name in self._providers:
                logger.warning("Provider already registered, overwriting", name=provider.name)
            self._providers[provider.name] = provider
            logger.info("Registered AI provider", name=provider.name, display_name=provider.display_name)

    def unregister(self, name: str) -> None:
        with self._lock:
            if name not in self._providers:
                raise ProviderNotFoundError(f"Provider '{name}' is not registered.")
            del self._providers[name]
            logger.info("Unregistered AI provider", name=name)

    def resolve(self, name: str) -> AIProvider:
        with self._lock:
            provider = self._providers.get(name)
            if provider is None:
                registered = list(self._providers.keys())
                raise ProviderNotFoundError(
                    f"AI provider '{name}' is not registered. Registered providers: {registered}"
                )
            return provider

    def list_providers(self) -> list[str]:
        with self._lock:
            return list(self._providers.keys())

    async def get_provider_info(self, name: str) -> ProviderInfo:
        provider = self.resolve(name)
        return await provider.provider_info()

    def is_registered(self, name: str) -> bool:
        with self._lock:
            return name in self._providers

    def count(self) -> int:
        with self._lock:
            return len(self._providers)

    def clear(self) -> None:
        with self._lock:
            self._providers.clear()
