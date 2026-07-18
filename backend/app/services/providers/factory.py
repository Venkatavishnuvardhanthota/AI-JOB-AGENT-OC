"""Provider Factory - creates and registers provider instances."""

import logging

from app.services.providers.base import BaseProvider
from app.services.providers.config import PROVIDER_CONFIGS, ProviderSettings
from app.services.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Creates provider instances and registers them with the registry."""

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()
        self._provider_classes: dict[str, type[BaseProvider]] = {}

    def register_class(self, name: str, cls: type[BaseProvider]) -> None:
        """Register a provider class for later instantiation."""
        self._provider_classes[name] = cls
        logger.debug("Registered provider class: %s -> %s", name, cls.__name__)

    def create(self, name: str, settings: ProviderSettings | None = None) -> BaseProvider:
        """Create a single provider instance and register it."""
        if name not in self._provider_classes:
            raise ValueError(
                f"No provider class registered for '{name}'. "
                f"Available: {list(self._provider_classes)}"
            )
        cls = self._provider_classes[name]
        if settings is None:
            settings = PROVIDER_CONFIGS.get(name)
        provider = cls(settings=settings)
        self.registry.register(provider)
        return provider

    def create_all(self, names: list[str] | None = None) -> dict[str, BaseProvider]:
        """Create and register providers. If names is None, creates all registered."""
        target_names = names or list(self._provider_classes.keys())
        created: dict[str, BaseProvider] = {}
        for name in target_names:
            if name not in self._provider_classes:
                logger.warning("Skipping unknown provider '%s'", name)
                continue
            try:
                provider = self.create(name)
                created[name] = provider
            except Exception:
                logger.exception("Failed to create provider '%s'", name)
        return created


_default_factory: ProviderFactory | None = None


def get_provider_factory() -> ProviderFactory:
    """Get or create the default provider factory singleton."""
    global _default_factory
    if _default_factory is None:
        _default_factory = ProviderFactory()
    return _default_factory
