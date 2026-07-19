import logging

from app.services.llm.anthropic_client import AnthropicClient
from app.services.llm.base import BaseLLMClient
from app.services.llm.config import LLMProviderItem, llm_config
from app.services.llm.gemini_client import GeminiClient
from app.services.llm.ollama import OllamaClient
from app.services.llm.openai_client import OpenAIClient
from app.services.llm.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)

_client_registry: dict[str, BaseLLMClient] = {}


def _build_client(cfg: LLMProviderItem) -> BaseLLMClient | None:
    if not cfg.enabled:
        return None
    if cfg.provider == "openai":
        return OpenAIClient(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            timeout=cfg.timeout,
        )
    elif cfg.provider == "anthropic":
        return AnthropicClient(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            timeout=cfg.timeout,
        )
    elif cfg.provider == "gemini":
        return GeminiClient(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            timeout=cfg.timeout,
        )
    elif cfg.provider == "ollama":
        return OllamaClient(
            base_url=cfg.base_url,
            timeout=cfg.timeout,
        )
    elif cfg.provider == "openrouter":
        return OpenRouterClient(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            timeout=cfg.timeout,
        )
    logger.warning("Unknown LLM provider: %s", cfg.provider)
    return None


def get_llm_client(provider: str | None = None) -> BaseLLMClient | None:
    provider = provider or llm_config.default_provider
    if provider in _client_registry:
        return _client_registry[provider]
    cfg = llm_config.providers.get(provider)
    if not cfg:
        logger.warning("LLM provider %s not configured", provider)
        return None
    client = _build_client(cfg)
    if client:
        _client_registry[provider] = client
    return client


def list_providers() -> list[str]:
    return [
        name for name, cfg in llm_config.providers.items()
        if cfg.enabled
    ]


async def close_clients():
    for client in _client_registry.values():
        try:
            if hasattr(client, "close"):
                await client.close()
        except Exception:
            logger.warning("Error closing LLM client", exc_info=True)
    _client_registry.clear()
