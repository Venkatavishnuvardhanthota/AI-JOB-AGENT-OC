from __future__ import annotations

import threading

import structlog

from app.jobs.exceptions import ProviderNotFoundError
from app.jobs.interfaces import JobProvider

logger = structlog.get_logger(__name__)


class JobProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, JobProvider] = {}
        self._lock = threading.Lock()

    def register(self, provider: JobProvider) -> None:
        with self._lock:
            if not provider.name:
                raise ValueError("Provider must have a non-empty name.")
            if provider.name in self._providers:
                logger.warning("Provider already registered, overwriting", name=provider.name)
            self._providers[provider.name] = provider
            logger.info("Registered job provider", name=provider.name, display_name=provider.display_name)

    def unregister(self, name: str) -> None:
        with self._lock:
            if name not in self._providers:
                raise ProviderNotFoundError(f"Job provider '{name}' is not registered.")
            del self._providers[name]
            logger.info("Unregistered job provider", name=name)

    def resolve(self, name: str) -> JobProvider:
        with self._lock:
            provider = self._providers.get(name)
            if provider is None:
                registered = list(self._providers.keys())
                raise ProviderNotFoundError(
                    f"Job provider '{name}' is not registered. Registered providers: {registered}"
                )
            return provider

    def list_providers(self) -> list[str]:
        with self._lock:
            return list(self._providers.keys())

    def is_registered(self, name: str) -> bool:
        with self._lock:
            return name in self._providers

    def count(self) -> int:
        with self._lock:
            return len(self._providers)

    def clear(self) -> None:
        with self._lock:
            self._providers.clear()
