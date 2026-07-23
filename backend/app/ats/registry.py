from __future__ import annotations

import threading
from typing import Any

import structlog

from app.ats.exceptions import ATSProviderDuplicateError, ATSProviderNotFoundError
from app.ats.interfaces import ATSProvider
from app.ats.schemas import ATSDetectionResult

logger = structlog.get_logger(__name__)


class ATSProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ATSProvider] = {}
        self._lock = threading.Lock()

    def register(self, provider: ATSProvider) -> None:
        with self._lock:
            if not provider.name:
                raise ValueError("ATS provider must have a non-empty name.")
            if provider.name in self._providers:
                raise ATSProviderDuplicateError(f"ATS provider '{provider.name}' is already registered.")
            self._providers[provider.name] = provider
            logger.info("Registered ATS provider", name=provider.name, display_name=provider.display_name)

    def register_or_replace(self, provider: ATSProvider) -> None:
        with self._lock:
            if not provider.name:
                raise ValueError("ATS provider must have a non-empty name.")
            self._providers[provider.name] = provider
            logger.info("Registered (or replaced) ATS provider", name=provider.name)

    def unregister(self, name: str) -> None:
        with self._lock:
            if name not in self._providers:
                raise ATSProviderNotFoundError(f"ATS provider '{name}' is not registered.")
            del self._providers[name]
            logger.info("Unregistered ATS provider", name=name)

    def resolve(self, name: str) -> ATSProvider:
        with self._lock:
            provider = self._providers.get(name)
            if provider is None:
                registered = list(self._providers.keys())
                raise ATSProviderNotFoundError(f"ATS provider '{name}' is not registered. Registered: {registered}")
            return provider

    def detect(self, url: str) -> ATSProvider | None:
        with self._lock:
            for provider in self._providers.values():
                if provider.supports(url):
                    return provider
            return None

    def detect_result(self, url: str) -> ATSDetectionResult | None:
        with self._lock:
            for provider in self._providers.values():
                result = provider.detect(url)
                if result is not None:
                    return result
            return None

    def list_providers(self) -> list[str]:
        with self._lock:
            return list(self._providers.keys())

    def list_details(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "name": p.name,
                    "display_name": p.display_name,
                    "description": p.description,
                    "version": p.version,
                    "capabilities": [c.value for c in p.capabilities()],
                    "url_patterns": p.url_patterns if hasattr(p, "url_patterns") else [],
                    "requires_login": p.requires_login,
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
