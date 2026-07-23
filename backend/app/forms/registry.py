from __future__ import annotations

from typing import Any

import structlog

from app.forms.exceptions import FormProviderNotFoundError

logger = structlog.get_logger(__name__)


class FormProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}
        self._logger = logger.bind(service="form_registry")

    def register(self, name: str, provider: Any) -> None:
        self._providers[name] = provider
        self._logger.info("Registered form provider", name=name)

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)

    def resolve(self, name: str) -> Any:
        provider = self._providers.get(name)
        if provider is None:
            raise FormProviderNotFoundError(f"Form provider '{name}' not found")
        return provider

    def is_registered(self, name: str) -> bool:
        return name in self._providers

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def clear(self) -> None:
        self._providers.clear()

    def count(self) -> int:
        return len(self._providers)
