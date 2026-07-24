from __future__ import annotations

from functools import lru_cache

from app.ai.config import AIConfig
from app.ai.prompts.registry import PromptTemplateRegistry
from app.ai.registry import AIProviderRegistry
from app.ai.service import AIService


@lru_cache
def _get_registry() -> AIProviderRegistry:
    return AIProviderRegistry()


@lru_cache
def _get_config() -> AIConfig:
    from app.core.config import settings

    return AIConfig(
        default_provider=settings.AI_DEFAULT_PROVIDER,
        default_model=settings.AI_DEFAULT_MODEL,
        fallback_model=settings.AI_FALLBACK_MODEL,
        fallback_provider=settings.AI_FALLBACK_PROVIDER or None,
        max_retries=settings.AI_MAX_RETRIES,
        timeout_seconds=settings.AI_TIMEOUT_SECONDS,
        temperature=settings.AI_TEMPERATURE,
        max_tokens=settings.AI_MAX_TOKENS,
        enabled_providers=settings.ENABLED_JOB_PROVIDERS,
        openrouter_api_key=settings.OPENROUTER_API_KEY,
        openrouter_base_url=settings.OPENROUTER_BASE_URL,
        openrouter_default_model=settings.OPENROUTER_DEFAULT_MODEL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        ollama_default_model=settings.OLLAMA_DEFAULT_MODEL,
    )


def get_registry() -> AIProviderRegistry:
    return _get_registry()


def get_ai_config() -> AIConfig:
    return _get_config()


def ensure_providers_registered() -> None:
    from app.ai.factory import AIProviderFactory

    registry = _get_registry()
    if registry.count() == 0:
        config = _get_config()
        factory = AIProviderFactory(registry, config)
        factory.register_all()


@lru_cache
def _get_prompt_registry() -> PromptTemplateRegistry:
    return PromptTemplateRegistry()


def get_prompt_registry() -> PromptTemplateRegistry:
    return _get_prompt_registry()


def get_ai_service() -> AIService:
    registry = _get_registry()
    config = _get_config()
    prompt_registry = _get_prompt_registry()
    ensure_providers_registered()
    return AIService(registry=registry, config=config, prompt_registry=prompt_registry)
