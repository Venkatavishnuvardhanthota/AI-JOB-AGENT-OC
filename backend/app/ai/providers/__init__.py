from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.openrouter import OpenRouterProvider

try:
    from app.ai.providers.anthropic_provider import AnthropicProvider
except Exception:
    AnthropicProvider = None  # type: ignore

try:
    from app.ai.providers.gemini_provider import GeminiProvider
except Exception:
    GeminiProvider = None  # type: ignore


__all__ = [
    "OllamaProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "AnthropicProvider",
    "GeminiProvider",
]
