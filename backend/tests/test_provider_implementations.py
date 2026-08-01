"""Tests for all AI provider implementations and infrastructure."""


import pytest
import structlog

from app.ai.config import AIConfig
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.registry import AIProviderRegistry
from app.ai.schemas import CapabilityInfo
from app.ai.service import AIService

logger = structlog.get_logger(__name__)


class TestAllProviderImplementations:
    """Verify every provider class can be instantiated and has correct metadata."""

    def test_openrouter_metadata(self):
        config = AIConfig(openrouter_api_key="test-key")
        provider = OpenRouterProvider(config)
        assert provider.name == "openrouter"
        assert provider.display_name == "OpenRouter"
        assert provider.version == "1.0.0"
        assert provider.supports_streaming is True
        caps = provider.capabilities
        assert caps.chat is True
        assert caps.streaming is True
        assert caps.vision is True

    def test_openrouter_validate_config_missing_key(self):
        config = AIConfig(openrouter_api_key=None)
        provider = OpenRouterProvider(config)
        errors = provider.validate_config()
        assert len(errors) > 0
        assert "OPENROUTER_API_KEY" in errors[0]

    def test_openrouter_validate_config_ok(self):
        config = AIConfig(openrouter_api_key="sk-test")
        provider = OpenRouterProvider(config)
        errors = provider.validate_config()
        assert len(errors) == 0

    def test_openai_metadata(self):
        config = AIConfig(openai_api_key="test-key")
        provider = OpenAIProvider(config)
        assert provider.name == "openai"
        assert provider.display_name == "OpenAI"
        assert provider.supports_streaming is True
        caps = provider.capabilities
        assert caps.chat is True
        assert caps.json_mode is True
        assert caps.function_calling is True
        assert caps.structured_output is True

    def test_openai_validate_config_missing_key(self):
        provider = OpenAIProvider(AIConfig(openai_api_key=None))
        errors = provider.validate_config()
        assert len(errors) > 0

    def test_openai_validate_config_ok(self):
        provider = OpenAIProvider(AIConfig(openai_api_key="sk-test"))
        errors = provider.validate_config()
        assert len(errors) == 0

    def test_anthropic_metadata(self):
        config = AIConfig(anthropic_api_key="test-key")
        provider = AnthropicProvider(config)
        assert provider.name == "anthropic"
        assert provider.display_name == "Anthropic"
        assert provider.supports_streaming is True
        caps = provider.capabilities
        assert caps.reasoning is True
        assert caps.vision is True
        assert caps.tool_calling is True

    def test_anthropic_validate_config_missing_key(self):
        provider = AnthropicProvider(AIConfig(anthropic_api_key=None))
        errors = provider.validate_config()
        assert len(errors) > 0

    def test_anthropic_validate_config_ok(self):
        provider = AnthropicProvider(AIConfig(anthropic_api_key="sk-ant-test"))
        errors = provider.validate_config()
        assert len(errors) == 0

    def test_anthropic_available_models(self):
        provider = AnthropicProvider(AIConfig(anthropic_api_key="test"))
        import asyncio
        models = asyncio.run(provider.available_models())
        assert len(models) > 0
        assert any(m.id == "claude-sonnet-4-20250514" for m in models)
        assert any(m.supports_vision for m in models)
        assert any(m.supports_reasoning for m in models)

    def test_gemini_metadata(self):
        config = AIConfig(gemini_api_key="test-key")
        provider = GeminiProvider(config)
        assert provider.name == "gemini"
        assert provider.display_name == "Gemini"
        caps = provider.capabilities
        assert caps.vision is True
        assert caps.structured_output is True

    def test_gemini_validate_config_missing_key(self):
        provider = GeminiProvider(AIConfig(gemini_api_key=None))
        errors = provider.validate_config()
        assert len(errors) > 0

    def test_gemini_validate_config_ok(self):
        provider = GeminiProvider(AIConfig(gemini_api_key="ai-test"))
        errors = provider.validate_config()
        assert len(errors) == 0

    def test_gemini_available_models(self):
        provider = GeminiProvider(AIConfig(gemini_api_key="test"))
        import asyncio
        models = asyncio.run(provider.available_models())
        assert len(models) > 0
        assert any("gemini" in m.id for m in models)

    def test_ollama_metadata(self):
        provider = OllamaProvider(AIConfig())
        assert provider.name == "ollama"
        assert provider.display_name == "Ollama"
        caps = provider.capabilities
        assert caps.chat is True
        assert caps.streaming is False
        assert caps.vision is False

    def test_ollama_validate_config(self):
        provider = OllamaProvider(AIConfig())
        errors = provider.validate_config()
        assert len(errors) == 0

    def test_all_providers_have_required_attributes(self):
        config = AIConfig(
            openrouter_api_key="k1",
            openai_api_key="k2",
            anthropic_api_key="k3",
            gemini_api_key="k4",
        )
        providers = [
            OpenRouterProvider(config),
            OpenAIProvider(config),
            AnthropicProvider(config),
            GeminiProvider(config),
            OllamaProvider(config),
        ]
        for p in providers:
            assert p.name, f"Provider {p.__class__.__name__} missing name"
            assert p.display_name, f"Provider {p.__class__.__name__} missing display_name"
            assert hasattr(p, "capabilities"), f"Provider {p.__class__.__name__} missing capabilities"
            assert hasattr(p, "validate_config"), f"Provider {p.__class__.__name__} missing validate_config"
            assert hasattr(p, "generate"), f"Provider {p.__class__.__name__} missing generate"
            assert hasattr(p, "health_check"), f"Provider {p.__class__.__name__} missing health_check"
            assert hasattr(p, "available_models"), f"Provider {p.__class__.__name__} missing available_models"
            assert hasattr(p, "provider_info"), f"Provider {p.__class__.__name__} missing provider_info"


class TestExtendedRegistry:
    def test_register_all_providers(self):
        registry = AIProviderRegistry()
        config = AIConfig(
            enabled_providers=["openrouter", "openai", "anthropic", "gemini", "ollama"],
            openrouter_api_key="k1",
            openai_api_key="k2",
            anthropic_api_key="k3",
            gemini_api_key="k4",
        )
        from app.ai.factory import AIProviderFactory
        factory = AIProviderFactory(registry, config)
        factory.register_all()
        assert registry.count() == 5
        assert registry.is_registered("openrouter")
        assert registry.is_registered("openai")
        assert registry.is_registered("anthropic")
        assert registry.is_registered("gemini")
        assert registry.is_registered("ollama")

    def test_get_all_provider_infos(self):
        registry = AIProviderRegistry()
        config = AIConfig(
            enabled_providers=["openrouter", "ollama"],
        )
        from app.ai.factory import AIProviderFactory
        factory = AIProviderFactory(registry, config)
        factory.register_all()

        import asyncio
        infos = asyncio.run(registry.get_all_provider_infos(default_provider="openrouter"))
        assert "openrouter" in infos
        info = infos["openrouter"]
        assert info.name == "openrouter"
        assert info.is_default is True
        assert isinstance(info.capabilities, CapabilityInfo)

    def test_provider_status_methods(self):
        registry = AIProviderRegistry()
        config = AIConfig(enabled_providers=["openrouter", "ollama"])
        from app.ai.factory import AIProviderFactory
        factory = AIProviderFactory(registry, config)
        factory.register_all()

        assert registry.count() == len(registry.list_providers())
        assert registry.is_registered("openrouter")
        assert not registry.is_registered("nonexistent")


class TestExtendedAIService:
    @pytest.fixture
    def config(self) -> AIConfig:
        return AIConfig(
            default_provider="openrouter",
            default_model="gpt-4o",
        )

    @pytest.fixture
    def registry(self) -> AIProviderRegistry:
        r = AIProviderRegistry()
        from app.ai.factory import AIProviderFactory
        factory = AIProviderFactory(r, AIConfig(enabled_providers=["openrouter"]))
        factory.register_all()
        return r

    @pytest.fixture
    def service(self, registry: AIProviderRegistry, config: AIConfig) -> AIService:
        return AIService(registry=registry, config=config)

    @pytest.mark.asyncio
    async def test_generate_text_convenience(self):
        from tests.test_ai import MockProvider
        registry = AIProviderRegistry()
        registry.register(MockProvider(AIConfig()))
        config = AIConfig(default_provider="mock", default_model="mock-model")
        service = AIService(registry=registry, config=config)
        result = await service.generate_text("Hello AI")
        assert result == "Echo: Hello AI"

    @pytest.mark.asyncio
    async def test_detailed_health(self, service: AIService):
        results = await service.detailed_health()
        assert len(results) > 0
        for r in results:
            assert r.provider is not None
            assert isinstance(r.healthy, bool)
            assert isinstance(r.configured, bool)
            assert isinstance(r.is_default, bool)

    @pytest.mark.asyncio
    async def test_detailed_health_specific(self, service: AIService):
        results = await service.detailed_health(provider_name="openrouter")
        assert len(results) == 1
        assert results[0].provider == "openrouter"

    @pytest.mark.asyncio
    async def test_detailed_health_nonexistent(self, service: AIService):
        results = await service.detailed_health(provider_name="nonexistent")
        assert len(results) == 1
        assert results[0].healthy is False
        assert results[0].error is not None

    def test_all_provider_info(self, service: AIService):
        import asyncio
        infos = asyncio.run(service.all_provider_info())
        assert len(infos) > 0
        for name, info in infos.items():
            assert info.name == name
            assert isinstance(info.capabilities, CapabilityInfo)


class TestAIConfigExtended:
    def test_new_fields(self):
        cfg = AIConfig()
        assert cfg.retry_delay_seconds == 1
        assert cfg.streaming_enabled is False

    def test_new_api_key_fields(self):
        cfg = AIConfig(
            openai_api_key="sk-test",
            anthropic_api_key="sk-ant-test",
            gemini_api_key="ai-test",
        )
        assert cfg.openai_api_key == "sk-test"
        assert cfg.anthropic_api_key == "sk-ant-test"
        assert cfg.gemini_api_key == "ai-test"

    def test_new_provider_defaults(self):
        cfg = AIConfig()
        assert cfg.openai_base_url == "https://api.openai.com"
        assert cfg.openai_default_model == "gpt-4o"
        assert cfg.anthropic_base_url == "https://api.anthropic.com"
        assert cfg.anthropic_default_model == "claude-sonnet-4-20250514"
        assert cfg.gemini_base_url == "https://generativelanguage.googleapis.com"
        assert cfg.gemini_default_model == "gemini-2.0-flash"
