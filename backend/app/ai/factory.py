from __future__ import annotations

import structlog

from app.ai.config import AIConfig
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.registry import AIProviderRegistry

logger = structlog.get_logger(__name__)

KNOWN_AI_PROVIDERS: set[str] = {"openrouter", "ollama", "openai", "anthropic", "gemini"}
IMPLEMENTED_AI_PROVIDERS: set[str] = {"openrouter", "ollama", "openai", "anthropic", "gemini"}


class AIProviderFactory:
    def __init__(self, registry: AIProviderRegistry, config: AIConfig) -> None:
        self._registry = registry
        self._config = config

    def register_all(self) -> None:
        configured = [p.lower().strip() for p in self._config.enabled_providers]
        configured_set = set(configured)
        duplicates = len(configured) - len(configured_set)
        if duplicates:
            logger.warning("Duplicate AI provider names in configuration", count=duplicates)

        invalid = configured_set - KNOWN_AI_PROVIDERS
        for name in sorted(invalid):
            logger.warning("Invalid AI provider name", provider=name)

        not_implemented = (configured_set & KNOWN_AI_PROVIDERS) - IMPLEMENTED_AI_PROVIDERS
        for name in sorted(not_implemented):
            logger.warning("AI provider not implemented", provider=name)

        registrations = [
            ("openrouter", self._register_openrouter),
            ("openai", self._register_openai),
            ("anthropic", self._register_anthropic),
            ("gemini", self._register_gemini),
            ("ollama", self._register_ollama),
        ]

        for name, register_fn in registrations:
            if name in configured_set:
                try:
                    register_fn()
                except Exception:
                    logger.exception("Failed to register AI provider", provider=name)

        registered = self._registry.list_providers()
        if not registered:
            logger.warning("No AI providers registered")
        else:
            logger.info("Registered AI providers", providers=registered)

    def _register_openrouter(self) -> None:
        errors = OpenRouterProvider(self._config).validate_config()
        if errors:
            logger.warning("OpenRouter provider configuration incomplete", errors=errors)
        provider = OpenRouterProvider(self._config)
        self._registry.register(provider)

    def _register_openai(self) -> None:
        errors = OpenAIProvider(self._config).validate_config()
        if errors:
            logger.warning("OpenAI provider configuration incomplete", errors=errors)
        provider = OpenAIProvider(self._config)
        self._registry.register(provider)

    def _register_anthropic(self) -> None:
        errors = AnthropicProvider(self._config).validate_config()
        if errors:
            logger.warning("Anthropic provider configuration incomplete", errors=errors)
        provider = AnthropicProvider(self._config)
        self._registry.register(provider)

    def _register_gemini(self) -> None:
        errors = GeminiProvider(self._config).validate_config()
        if errors:
            logger.warning("Gemini provider configuration incomplete", errors=errors)
        provider = GeminiProvider(self._config)
        self._registry.register(provider)

    def _register_ollama(self) -> None:
        provider = OllamaProvider(self._config)
        self._registry.register(provider)
