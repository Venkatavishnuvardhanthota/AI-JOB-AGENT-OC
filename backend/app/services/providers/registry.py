import logging
from typing import Any

from app.services.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ProviderNotFoundError(Exception):
    """Raised when a requested provider is not registered."""


class ProviderRegistry:
    """Registry of all available job providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        if provider.name in self._providers:
            logger.warning("Provider '%s' already registered, overwriting", provider.name)
        self._providers[provider.name] = provider
        logger.info("Registered provider: %s", provider.name)

    def get(self, name: str) -> BaseProvider:
        provider = self._providers.get(name)
        if provider is None:
            raise ProviderNotFoundError(f"Provider '{name}' not found. Available: {list(self._providers)}")
        return provider

    def get_enabled(self) -> dict[str, BaseProvider]:
        return {name: p for name, p in self._providers.items() if p.enabled}

    def get_all(self) -> dict[str, BaseProvider]:
        return dict(self._providers)

    async def search_all(self, query: str, **kwargs) -> dict[str, list[Any]]:
        results: dict[str, list[Any]] = {}
        for name, provider in self.get_enabled().items():
            try:
                jobs = await provider.search(query, **kwargs)
                results[name] = jobs
            except Exception:
                logger.exception("Provider '%s' search failed for query='%s'", name, query)
                results[name] = []
        return results

    async def close_all(self) -> None:
        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception:
                logger.exception("Error closing provider '%s'", provider.name)

    def __len__(self) -> int:
        return len(self._providers)


provider_registry = ProviderRegistry()
