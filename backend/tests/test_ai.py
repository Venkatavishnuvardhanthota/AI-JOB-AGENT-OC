import uuid
from collections.abc import AsyncIterator

import pytest
import structlog

from app.ai.config import AIConfig
from app.ai.dependencies import _get_registry, get_ai_config, get_ai_service
from app.ai.exceptions import (
    AIError,
    AIServiceValidationError,
    ConfigurationError,
    GenerationError,
    ModelUnavailableError,
    ProviderNotFoundError,
    ProviderUnavailableError,
    TimeoutError,
)
from app.ai.interfaces import AIProvider
from app.ai.registry import AIProviderRegistry
from app.ai.schemas import AIRequest, AIResponse, GenerationMetadata, ModelInfo, ProviderInfo, UsageMetrics
from app.ai.service import AIService

logger = structlog.get_logger(__name__)


# ── Mock Provider ──


class MockProvider(AIProvider):
    name = "mock"
    display_name = "Mock Provider"
    description = "A mock provider for testing"
    supports_streaming = True

    async def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            content=f"Echo: {request.prompt[:20]}",
            model=request.model or "mock-model",
            provider=self.name,
            usage=UsageMetrics(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata=GenerationMetadata(model=request.model or "mock-model", provider=self.name, finish_reason="stop"),
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        content = f"Echo: {request.prompt[:20]}"
        for chunk in content.split(" "):
            yield chunk + " "

    async def health_check(self) -> bool:
        return True

    async def available_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(id="mock-model", name="Mock Model", provider=self.name, max_tokens=4096),
        ]

    async def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            is_available=True,
            version="1.0.0",
            supports_streaming=self.supports_streaming,
            models=await self.available_models(),
        )


class FailingMockProvider(AIProvider):
    name = "failing"
    display_name = "Failing Provider"

    async def generate(self, request: AIRequest) -> AIResponse:
        raise GenerationError("Mock generation failure")

    async def health_check(self) -> bool:
        return False

    async def available_models(self) -> list[ModelInfo]:
        raise ModelUnavailableError("Models not available")

    async def provider_info(self) -> ProviderInfo:
        return ProviderInfo(name=self.name, display_name=self.display_name, is_available=False)


class EmptyProvider(AIProvider):
    name = ""
    display_name = "Empty"

    async def generate(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError

    async def health_check(self) -> bool:
        return False

    async def available_models(self) -> list[ModelInfo]:
        return []

    async def provider_info(self) -> ProviderInfo:
        return ProviderInfo(name=self.name, display_name=self.display_name)


# ── Fixtures ──


@pytest.fixture
def config() -> AIConfig:
    return AIConfig(
        default_provider="mock",
        default_model="mock-model",
    )


@pytest.fixture
def registry() -> AIProviderRegistry:
    r = AIProviderRegistry()
    r.register(MockProvider(AIConfig()))
    return r


@pytest.fixture
def registry_with_failing() -> AIProviderRegistry:
    r = AIProviderRegistry()
    r.register(MockProvider(AIConfig()))
    r.register(FailingMockProvider(AIConfig()))
    return r


@pytest.fixture
def service(registry: AIProviderRegistry, config: AIConfig) -> AIService:
    return AIService(registry=registry, config=config)


@pytest.fixture
def service_with_failing(registry_with_failing: AIProviderRegistry, config: AIConfig) -> AIService:
    return AIService(registry=registry_with_failing, config=config)


@pytest.fixture
def fallback_service(registry_with_failing: AIProviderRegistry) -> AIService:
    return AIService(
        registry=registry_with_failing,
        config=AIConfig(
            default_provider="failing",
            default_model="primary-model",
            fallback_provider="mock",
            fallback_model="fallback-model",
        ),
    )


# ── AI Exceptions ──


class TestAIExceptions:
    def test_ai_error_base(self):
        exc = AIError()
        assert exc.status_code == 502
        assert exc.code == "AI_ERROR"

    def test_ai_error_with_message(self):
        exc = AIError("Custom message", details={"key": "val"})
        assert exc.message == "Custom message"
        assert exc.details == {"key": "val"}

    def test_provider_unavailable(self):
        exc = ProviderUnavailableError()
        assert exc.status_code == 502
        assert exc.code == "PROVIDER_UNAVAILABLE"

    def test_provider_not_found(self):
        exc = ProviderNotFoundError()
        assert exc.status_code == 404
        assert exc.code == "PROVIDER_NOT_FOUND"

    def test_model_unavailable(self):
        exc = ModelUnavailableError()
        assert exc.code == "MODEL_UNAVAILABLE"

    def test_generation_error(self):
        exc = GenerationError()
        assert exc.code == "GENERATION_ERROR"

    def test_timeout_error(self):
        exc = TimeoutError()
        assert exc.status_code == 504
        assert exc.code == "AI_TIMEOUT"

    def test_configuration_error(self):
        exc = ConfigurationError()
        assert exc.status_code == 500
        assert exc.code == "AI_CONFIGURATION_ERROR"

    def test_validation_error(self):
        exc = AIServiceValidationError()
        assert exc.status_code == 400
        assert exc.code == "AI_VALIDATION_ERROR"


# ── AI Config ──


class TestAIConfig:
    def test_default_config(self):
        cfg = AIConfig()
        assert cfg.default_provider == "openrouter"
        assert cfg.default_model == "gpt-4o"
        assert cfg.max_retries == 3
        assert cfg.timeout_seconds == 60
        assert cfg.temperature is None
        assert cfg.max_tokens is None

    def test_custom_config(self):
        cfg = AIConfig(default_provider="custom", default_model="custom-model", temperature=0.5, max_tokens=1000)
        assert cfg.default_provider == "custom"
        assert cfg.temperature == 0.5
        assert cfg.max_tokens == 1000

    def test_temperature_validation(self):
        with pytest.raises(Exception):
            AIConfig(temperature=3.0)

        with pytest.raises(Exception):
            AIConfig(temperature=-0.5)


# ── AI Schemas ──


class TestAIRequest:
    def test_default_request(self):
        req = AIRequest(prompt="Hello")
        assert req.prompt == "Hello"
        assert req.system_prompt is None
        assert req.model is None
        assert req.temperature is None

    def test_full_request(self):
        req = AIRequest(
            prompt="Write a poem",
            system_prompt="You are a poet",
            model="gpt-4o",
            temperature=0.8,
            max_tokens=500,
            provider="openai",
            stop_sequences=["\n\n"],
        )
        assert req.model == "gpt-4o"
        assert req.temperature == 0.8
        assert req.stop_sequences == ["\n\n"]

    def test_empty_prompt_raises(self):
        with pytest.raises(Exception):
            AIRequest(prompt="")


class TestAIResponse:
    def test_default_response(self):
        resp = AIResponse(content="Hello", model="gpt-4o", provider="openai")
        assert resp.content == "Hello"
        assert isinstance(resp.id, uuid.UUID)
        assert resp.usage.prompt_tokens is None
        assert resp.metadata is None

    def test_full_response(self):
        resp = AIResponse(
            content="Result",
            model="gpt-4o",
            provider="openai",
            usage=UsageMetrics(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            metadata=GenerationMetadata(model="gpt-4o", provider="openai", finish_reason="stop"),
        )
        assert resp.usage.total_tokens == 150
        assert resp.metadata.finish_reason == "stop"


class TestModelInfo:
    def test_defaults(self):
        info = ModelInfo(id="m1", name="Model 1", provider="test")
        assert info.supports_streaming is False
        assert info.supports_function_calling is False
        assert info.supports_vision is False
        assert info.max_tokens is None


class TestUsageMetrics:
    def test_defaults(self):
        m = UsageMetrics()
        assert m.prompt_tokens is None
        assert m.completion_tokens is None
        assert m.total_tokens is None
        assert m.estimated_cost is None


# ── Provider Registry ──


class TestAIProviderRegistry:
    def test_register_and_resolve(self, registry: AIProviderRegistry):
        assert registry.is_registered("mock")
        provider = registry.resolve("mock")
        assert provider.name == "mock"
        assert provider.display_name == "Mock Provider"

    def test_resolve_nonexistent(self, registry: AIProviderRegistry):
        with pytest.raises(ProviderNotFoundError) as exc:
            registry.resolve("nonexistent")
        assert "nonexistent" in str(exc.value.message)

    def test_register_duplicate_overwrites(self, registry: AIProviderRegistry):
        new_mock = MockProvider(AIConfig())
        registry.register(new_mock)
        assert registry.count() == 1  # overwrites, no duplicate entry

    def test_register_empty_name_raises(self):
        registry = AIProviderRegistry()
        with pytest.raises(ConfigurationError):
            registry.register(EmptyProvider(AIConfig()))

    def test_unregister(self, registry: AIProviderRegistry):
        registry.unregister("mock")
        assert not registry.is_registered("mock")
        assert registry.count() == 0

    def test_unregister_nonexistent(self, registry: AIProviderRegistry):
        with pytest.raises(ProviderNotFoundError):
            registry.unregister("nonexistent")

    def test_list_providers(self, registry: AIProviderRegistry):
        names = registry.list_providers()
        assert "mock" in names

    def test_count(self, registry: AIProviderRegistry):
        assert registry.count() == 1

    def test_clear(self, registry: AIProviderRegistry):
        registry.clear()
        assert registry.count() == 0
        assert registry.list_providers() == []

    @pytest.mark.asyncio
    async def test_get_provider_info(self, registry: AIProviderRegistry):
        info = await registry.get_provider_info("mock")
        assert info.name == "mock"
        assert info.is_available is True

    @pytest.mark.asyncio
    async def test_get_provider_info_nonexistent(self, registry: AIProviderRegistry):
        with pytest.raises(ProviderNotFoundError):
            await registry.get_provider_info("nonexistent")

    def test_thread_safety(self, registry: AIProviderRegistry):
        import concurrent.futures

        def resolve_mock():
            return registry.resolve("mock")

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(resolve_mock) for _ in range(100)]
            for f in concurrent.futures.as_completed(futures):
                provider = f.result()
                assert provider.name == "mock"


# ── AI Service ──


class TestAIService:
    @pytest.mark.asyncio
    async def test_generate_success(self, service: AIService):
        response = await service.generate(AIRequest(prompt="Hello"))
        assert response.content == "Echo: Hello"
        assert response.provider == "mock"
        assert response.usage.prompt_tokens == 10

    @pytest.mark.asyncio
    async def test_generate_with_custom_provider(self, service: AIService):
        response = await service.generate(AIRequest(prompt="Hello", provider="mock"))
        assert response.provider == "mock"

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self, service: AIService):
        response = await service.generate(AIRequest(prompt="Hello", model="custom-model"))
        assert response.model == "custom-model"

    @pytest.mark.asyncio
    async def test_generate_empty_prompt_raises(self, service: AIService):
        with pytest.raises(AIServiceValidationError) as exc:
            await service.generate(AIRequest(prompt="   "))
        assert "empty" in str(exc.value.message).lower()

    @pytest.mark.asyncio
    async def test_generate_nonexistent_provider(self, service: AIService):
        with pytest.raises(ProviderNotFoundError):
            await service.generate(AIRequest(prompt="Hello", provider="nonexistent"))

    @pytest.mark.asyncio
    async def test_generate_with_failing_provider(self, service_with_failing: AIService):
        with pytest.raises(GenerationError):
            await service_with_failing.generate(AIRequest(prompt="Hello", provider="failing"))

    @pytest.mark.asyncio
    async def test_fallback_uses_fallback_model(self, fallback_service: AIService):
        response = await fallback_service.generate(AIRequest(prompt="Hello"))
        assert response.provider == "mock"
        assert response.model == "fallback-model"

    @pytest.mark.asyncio
    async def test_generate_stream(self, service: AIService):
        chunks = [chunk async for chunk in service.generate_stream(AIRequest(prompt="Hello world test"))]
        assert "".join(chunks).strip() == "Echo: Hello world test"

    def test_provider_param_override(self):
        cfg = AIConfig(provider_params={"mock": {"temperature": 0.3, "base_url": "http://custom"}})
        assert cfg.provider_param("mock", "temperature") == 0.3
        assert cfg.provider_param("mock", "base_url") == "http://custom"
        assert cfg.provider_param("mock", "max_tokens", default=99) == 99
        assert cfg.provider_param("mock", "api_key") is None

    def test_provider_param_env_fallback(self):
        cfg = AIConfig(openrouter_api_key="sk-env", provider_params={"openrouter": {}})
        assert cfg.provider_param("openrouter", "api_key") == "sk-env"

    @pytest.mark.asyncio
    async def test_health_check_all(self, service: AIService):
        results = await service.health_check()
        assert "mock" in results
        assert results["mock"] is True

    @pytest.mark.asyncio
    async def test_health_check_specific(self, service: AIService):
        results = await service.health_check(provider_name="mock")
        assert results["mock"] is True

    @pytest.mark.asyncio
    async def test_health_check_nonexistent(self, service: AIService):
        results = await service.health_check(provider_name="nonexistent")
        assert results["nonexistent"] is False

    @pytest.mark.asyncio
    async def test_health_check_failing(self, service_with_failing: AIService):
        results = await service_with_failing.health_check()
        assert results["mock"] is True
        assert results["failing"] is False

    @pytest.mark.asyncio
    async def test_available_models(self, service: AIService):
        results = await service.available_models()
        assert any(m.id == "mock-model" for m in results)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_available_models_specific(self, service: AIService):
        results = await service.available_models(provider_name="mock")
        assert len(results) == 1
        assert results[0].id == "mock-model"

    @pytest.mark.asyncio
    async def test_available_models_nonexistent(self, service: AIService):
        results = await service.available_models(provider_name="nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_available_models_failing(self, service_with_failing: AIService):
        results = await service_with_failing.available_models()
        assert any(m.id == "mock-model" for m in results)
        assert results[0].supports_json_mode is False
        assert results[0].supports_reasoning is False
        assert all(m.provider != "failing" for m in results)

    @pytest.mark.asyncio
    async def test_provider_info(self, service: AIService):
        info = await service.provider_info("mock")
        assert info.name == "mock"
        assert info.is_available is True
        assert len(info.models) == 1

    @pytest.mark.asyncio
    async def test_provider_info_nonexistent(self, service: AIService):
        with pytest.raises(ProviderNotFoundError):
            await service.provider_info("nonexistent")

    def test_list_providers(self, service: AIService):
        providers = service.list_providers()
        assert "mock" in providers

    def test_config_property(self, service: AIService, config: AIConfig):
        assert service.config is config


# ── AI Provider Interface ──


class TestAIProviderInterface:
    @pytest.mark.asyncio
    async def test_mock_provider_generate(self):
        provider = MockProvider(AIConfig())
        response = await provider.generate(AIRequest(prompt="Test"))
        assert response.content == "Echo: Test"
        assert response.provider == "mock"

    @pytest.mark.asyncio
    async def test_mock_provider_health_check(self):
        provider = MockProvider(AIConfig())
        assert await provider.health_check() is True

    @pytest.mark.asyncio
    async def test_mock_provider_available_models(self):
        provider = MockProvider(AIConfig())
        models = await provider.available_models()
        assert len(models) == 1
        assert models[0].id == "mock-model"

    @pytest.mark.asyncio
    async def test_mock_provider_info(self):
        provider = MockProvider(AIConfig())
        info = await provider.provider_info()
        assert info.name == "mock"
        assert info.is_available is True

    @pytest.mark.asyncio
    async def test_failing_provider_health_check(self):
        provider = FailingMockProvider(AIConfig())
        assert await provider.health_check() is False

    @pytest.mark.asyncio
    async def test_ai_provider_is_abstract(self):
        with pytest.raises(TypeError):
            AIProvider()  # type: ignore


# ── DI Integration ──


class TestAIDependencies:
    def test_get_registry_is_singleton(self):
        r1 = _get_registry()
        r2 = _get_registry()
        assert r1 is r2

    def test_get_config_singleton_until_applied(self):
        c1 = get_ai_config()
        c2 = get_ai_config()
        assert c1 is c2

    def test_get_ai_service(self):
        service = get_ai_service()
        assert isinstance(service, AIService)
        assert isinstance(service.config, AIConfig)
