from __future__ import annotations

import threading

import structlog

from app.integrations.exceptions import ConfigurationError, ProviderDuplicateError, ProviderNotFoundError
from app.integrations.interfaces import NotificationProvider

logger = structlog.get_logger(__name__)


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, NotificationProvider] = {}
        self._lock = threading.Lock()

    def register(self, provider: NotificationProvider) -> None:
        with self._lock:
            if not provider.name:
                raise ConfigurationError("Provider must have a non-empty name.")
            if provider.name in self._providers:
                raise ProviderDuplicateError(f"Provider '{provider.name}' is already registered.")
            self._providers[provider.name] = provider
            logger.info("Registered notification provider", name=provider.name)

    def register_or_replace(self, provider: NotificationProvider) -> None:
        with self._lock:
            if not provider.name:
                raise ConfigurationError("Provider must have a non-empty name.")
            self._providers[provider.name] = provider
            logger.info("Registered (or replaced) notification provider", name=provider.name)

    def unregister(self, name: str) -> None:
        with self._lock:
            if name not in self._providers:
                raise ProviderNotFoundError(f"Provider '{name}' is not registered.")
            del self._providers[name]
            logger.info("Unregistered notification provider", name=name)

    def resolve(self, name: str) -> NotificationProvider:
        with self._lock:
            provider = self._providers.get(name)
            if provider is None:
                registered = list(self._providers.keys())
                raise ProviderNotFoundError(
                    f"Notification provider '{name}' is not registered. Registered: {registered}"
                )
            return provider

    def list_providers(self) -> list[str]:
        with self._lock:
            return list(self._providers.keys())

    def list_details(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "name": p.name,
                    "display_name": p.display_name,
                    "description": p.description,
                    "version": p.version,
                    "channel": p.metadata().channel.value,
                }
                for p in self._providers.values()
            ]

    def is_registered(self, name: str) -> bool:
        with self._lock:
            return name in self._providers

    def count(self) -> int:
        with self._lock:
            return len(self._providers)

    def clear(self) -> None:
        with self._lock:
            self._providers.clear()
