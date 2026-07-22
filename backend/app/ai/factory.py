from __future__ import annotations

import structlog

from app.ai.config import AIConfig
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.registry import AIProviderRegistry

logger = structlog.get_logger(__name__)


class AIProviderFactory:
    def __init__(self, registry: AIProviderRegistry, config: AIConfig) -> None:
        self._registry = registry
        self._config = config

    def register_all(self) -> None:
        if "openrouter" in self._config.enabled_providers:
            self._register_openrouter()
        if "ollama" in self._config.enabled_providers:
            self._register_ollama()

        registered = self._registry.list_providers()
        if not registered:
            logger.warning("No AI providers registered")
        else:
            logger.info("Registered AI providers", providers=registered)

    def _register_openrouter(self) -> None:
        if not self._config.openrouter_api_key:
            logger.warning(
                "OpenRouter provider enabled but OPENROUTER_API_KEY is not set. "
                "Set OPENROUTER_API_KEY in environment or .env file."
            )
        provider = OpenRouterProvider(self._config)
        self._registry.register(provider)

    def _register_ollama(self) -> None:
        provider = OllamaProvider(self._config)
        self._registry.register(provider)
