import json

import httpx
import pytest
from httpx import MockTransport

from app.ai.config import AIConfig
from app.ai.exceptions import (
    GenerationError,
    ProviderNotFoundError,
    ProviderUnavailableError,
    TimeoutError,
)
from app.ai.http_client import AIHTTPClient
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.registry import AIProviderRegistry
from app.ai.schemas import AIRequest
from app.ai.service import AIService

pytestmark = pytest.mark.asyncio


def _make_transport(handler):
    return MockTransport(handler)


def _mock_client(handler):
    return httpx.AsyncClient(transport=_make_transport(handler), base_url="http://mock")


# ── Fixtures ──


@pytest.fixture
def openrouter_config() -> AIConfig:
    return AIConfig(
        default_provider="openrouter",
        default_model="gpt-4o",
        openrouter_api_key="sk-test-key",
        openrouter_base_url="https://openrouter.ai",
        timeout_seconds=30,
        max_retries=1,
    )


@pytest.fixture
def ollama_config() -> AIConfig:
    return AIConfig(
        default_provider="ollama",
        default_model="llama3",
        ollama_base_url="http://localhost:11434",
        timeout_seconds=30,
        max_retries=1,
    )


@pytest.fixture
def openrouter_provider(openrouter_config: AIConfig) -> OpenRouterProvider:
    return OpenRouterProvider(openrouter_config)


@pytest.fixture
def ollama_provider(ollama_config: AIConfig) -> OllamaProvider:
    return OllamaProvider(ollama_config)


@pytest.fixture
def registry_with_openrouter(openrouter_config: AIConfig) -> AIProviderRegistry:
    r = AIProviderRegistry()
    r.register(OpenRouterProvider(openrouter_config))
    return r


@pytest.fixture
def registry_with_ollama(ollama_config: AIConfig) -> AIProviderRegistry:
    r = AIProviderRegistry()
    r.register(OllamaProvider(ollama_config))
    return r


@pytest.fixture
def registry_with_both(openrouter_config: AIConfig, ollama_config: AIConfig) -> AIProviderRegistry:
    r = AIProviderRegistry()
    r.register(OpenRouterProvider(openrouter_config))
    r.register(OllamaProvider(ollama_config))
    return r


@pytest.fixture
def service_openrouter(registry_with_openrouter: AIProviderRegistry, openrouter_config: AIConfig) -> AIService:
    return AIService(registry=registry_with_openrouter, config=openrouter_config)


@pytest.fixture
def service_with_fallback(registry_with_both: AIProviderRegistry, openrouter_config: AIConfig) -> AIService:
    cfg = openrouter_config.model_copy(update={"fallback_provider": "ollama"})
    return AIService(registry=registry_with_both, config=cfg)


# ── HTTP Client Tests ──


class TestAIHTTPClient:
    async def test_post_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"result": "ok"})

        async with AIHTTPClient(base_url="http://mock", timeout_seconds=30, max_retries=1) as client:
            await client._client.aclose()
            client._client = _mock_client(handler)
            response = await client.post("/test", json={"key": "value"})
            assert response.json() == {"result": "ok"}

    async def test_post_401_raises_generation_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401)

        async with AIHTTPClient(base_url="http://mock", api_key="bad-key", timeout_seconds=30, max_retries=1) as client:
            await client._client.aclose()
            client._client = _mock_client(handler)
            with pytest.raises(GenerationError, match="Authentication failed"):
                await client.post("/test")

    async def test_post_400_raises_generation_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": {"message": "Bad model"}})

        async with AIHTTPClient(base_url="http://mock", timeout_seconds=30, max_retries=1) as client:
            await client._client.aclose()
            client._client = _mock_client(handler)
            with pytest.raises(GenerationError, match="Bad model"):
                await client.post("/test")

    async def test_post_timeout_retries_then_raises(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            raise httpx.TimeoutException("timeout")

        async with AIHTTPClient(base_url="http://mock", timeout_seconds=30, max_retries=2) as client:
            await client._client.aclose()
            client._client = _mock_client(handler)
            with pytest.raises(TimeoutError):
                await client.post("/test")
            assert call_count == 2

    async def test_post_connection_error_retries(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("connection refused")

        async with AIHTTPClient(base_url="http://mock", timeout_seconds=30, max_retries=2) as client:
            await client._client.aclose()
            client._client = _mock_client(handler)
            with pytest.raises(ProviderUnavailableError):
                await client.post("/test")
            assert call_count == 2

    async def test_post_500_retries_then_raises(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(500)

        async with AIHTTPClient(base_url="http://mock", timeout_seconds=30, max_retries=2) as client:
            await client._client.aclose()
            client._client = _mock_client(handler)
            with pytest.raises(ProviderUnavailableError):
                await client.post("/test")
            assert call_count == 2

    async def test_get_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[1, 2, 3])

        async with AIHTTPClient(base_url="http://mock", timeout_seconds=30, max_retries=1) as client:
            await client._client.aclose()
            client._client = _mock_client(handler)
            response = await client.get("/items")
            assert response.json() == [1, 2, 3]


# ── OpenRouter Provider Tests ──


class TestOpenRouterProvider:
    async def test_generate_success(self, openrouter_provider: OpenRouterProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["model"] == "gpt-4o"
            assert body["messages"][0]["role"] == "user"
            assert body["messages"][0]["content"] == "Hi"
            return httpx.Response(
                200,
                json={
                    "id": "gen-123",
                    "model": "gpt-4o",
                    "choices": [{"message": {"content": "Hello world"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                },
            )

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        response = await openrouter_provider.generate(AIRequest(prompt="Hi", model="gpt-4o"))

        assert response.content == "Hello world"
        assert response.model == "gpt-4o"
        assert response.provider == "openrouter"
        assert response.usage.prompt_tokens == 10
        assert response.usage.total_tokens == 30
        assert response.metadata.finish_reason == "stop"
        assert response.metadata.id == "gen-123"

    async def test_generate_with_system_prompt(self, openrouter_provider: OpenRouterProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert len(body["messages"]) == 2
            assert body["messages"][0]["role"] == "system"
            assert body["messages"][0]["content"] == "Be concise"
            assert body["messages"][1]["role"] == "user"
            return httpx.Response(
                200,
                json={
                    "id": "gen-456",
                    "model": "gpt-4o",
                    "choices": [{"message": {"content": "Sure!"}, "finish_reason": "stop"}],
                },
            )

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        response = await openrouter_provider.generate(
            AIRequest(prompt="Help me", system_prompt="Be concise", model="gpt-4o")
        )
        assert response.content == "Sure!"

    async def test_generate_with_temperature_and_max_tokens(self, openrouter_provider: OpenRouterProvider):
        sent_body = {}

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal sent_body
            sent_body = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "id": "gen-789",
                    "model": "gpt-4o",
                    "choices": [{"message": {"content": "Result"}, "finish_reason": "stop"}],
                },
            )

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        await openrouter_provider.generate(AIRequest(prompt="Test", model="gpt-4o", temperature=0.5, max_tokens=100))

        assert sent_body["temperature"] == 0.5
        assert sent_body["max_tokens"] == 100
        assert sent_body["model"] == "gpt-4o"

    async def test_generate_authentication_error(self, openrouter_provider: OpenRouterProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401)

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        with pytest.raises(GenerationError, match="Authentication failed"):
            await openrouter_provider.generate(AIRequest(prompt="Hi", model="gpt-4o"))

    async def test_health_check_success(self, openrouter_provider: OpenRouterProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": {"key": "valid"}})

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        assert await openrouter_provider.health_check() is True

    async def test_health_check_failure(self, openrouter_provider: OpenRouterProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401)

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        assert await openrouter_provider.health_check() is False

    async def test_available_models_success(self, openrouter_provider: OpenRouterProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "gpt-4o", "name": "GPT-4o", "context_length": 128000},
                        {"id": "claude-3-opus", "name": "Claude 3 Opus", "context_length": 200000},
                    ]
                },
            )

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        models = await openrouter_provider.available_models()
        assert len(models) == 2
        assert models[0].id == "gpt-4o"
        assert models[0].max_tokens == 128000
        assert models[1].id == "claude-3-opus"

    async def test_available_models_failure_returns_empty(self, openrouter_provider: OpenRouterProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        models = await openrouter_provider.available_models()
        assert models == []

    async def test_provider_info(self, openrouter_provider: OpenRouterProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            path = str(request.url)
            if "auth/key" in path:
                return httpx.Response(200, json={})
            if "/models" in path:
                return httpx.Response(200, json={"data": []})
            return httpx.Response(404)

        await openrouter_provider._client._client.aclose()
        openrouter_provider._client._client = _mock_client(handler)
        info = await openrouter_provider.provider_info()
        assert info.name == "openrouter"
        assert info.display_name == "OpenRouter"
        assert info.is_available is True
        assert info.supports_streaming is True


# ── Ollama Provider Tests ──


class TestOllamaProvider:
    async def test_generate_success(self, ollama_provider: OllamaProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["model"] == "llama3"
            assert body["stream"] is False
            return httpx.Response(
                200,
                json={
                    "model": "llama3",
                    "message": {"role": "assistant", "content": "Hello from Ollama"},
                    "done": True,
                    "done_reason": "stop",
                    "total_duration": 1_500_000_000,
                    "prompt_eval_count": 15,
                    "eval_count": 30,
                },
            )

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        response = await ollama_provider.generate(AIRequest(prompt="Hi", model="llama3"))

        assert response.content == "Hello from Ollama"
        assert response.model == "llama3"
        assert response.provider == "ollama"
        assert response.usage.prompt_tokens == 15
        assert response.usage.completion_tokens == 30
        assert response.usage.total_tokens == 45
        assert response.metadata.duration_ms == 1500

    async def test_generate_with_system_prompt(self, ollama_provider: OllamaProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert len(body["messages"]) == 2
            assert body["messages"][0]["role"] == "system"
            return httpx.Response(
                200,
                json={
                    "model": "llama3",
                    "message": {"content": "Response"},
                    "done": True,
                    "done_reason": "stop",
                },
            )

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        response = await ollama_provider.generate(AIRequest(prompt="Help", system_prompt="Be brief", model="llama3"))
        assert response.content == "Response"

    async def test_generate_no_usage(self, ollama_provider: OllamaProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "model": "llama3",
                    "message": {"content": "No usage"},
                    "done": True,
                },
            )

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        response = await ollama_provider.generate(AIRequest(prompt="Test", model="llama3"))
        assert response.usage.prompt_tokens is None
        assert response.usage.completion_tokens is None

    async def test_generate_with_temperature(self, ollama_provider: OllamaProvider):
        sent_body = {}

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal sent_body
            sent_body = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "model": "llama3",
                    "message": {"content": "Result"},
                    "done": True,
                },
            )

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        await ollama_provider.generate(AIRequest(prompt="Hi", model="llama3", temperature=0.7))

        assert sent_body["options"]["temperature"] == 0.7
        assert sent_body["stream"] is False

    async def test_generate_disables_reasoning_for_qwen3(self, ollama_provider: OllamaProvider):
        sent_body = {}

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal sent_body
            sent_body = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "model": "qwen3:8b",
                    "message": {"content": "Result"},
                    "done": True,
                },
            )

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        await ollama_provider.generate(AIRequest(prompt="Hi", model="qwen3:8b"))

        assert sent_body["think"] is False
        assert sent_body["stream"] is False

    async def test_generate_does_not_send_think_for_other_models(self, ollama_provider: OllamaProvider):
        sent_body = {}

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal sent_body
            sent_body = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "model": "llama3",
                    "message": {"content": "Result"},
                    "done": True,
                },
            )

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        await ollama_provider.generate(AIRequest(prompt="Hi", model="llama3"))

        assert "think" not in sent_body

    async def test_health_check_success(self, ollama_provider: OllamaProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": []})

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        assert await ollama_provider.health_check() is True

    async def test_health_check_failure(self, ollama_provider: OllamaProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(502)

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        assert await ollama_provider.health_check() is False

    async def test_available_models_success(self, ollama_provider: OllamaProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "llama3:latest", "details": {"family": "llama"}},
                        {"name": "mistral:latest", "details": {"family": "mistral"}},
                    ]
                },
            )

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        models = await ollama_provider.available_models()
        assert len(models) == 2
        assert models[0].id == "llama3:latest"
        assert models[0].supports_function_calling is True

    async def test_available_models_failure_returns_empty(self, ollama_provider: OllamaProvider):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        models = await ollama_provider.available_models()
        assert models == []

    async def test_provider_info(self, ollama_provider: OllamaProvider):
        called_paths = []

        def handler(request: httpx.Request) -> httpx.Response:
            called_paths.append(str(request.url))
            return httpx.Response(
                200,
                json={"models": [{"name": "llama3", "details": {"family": "llama"}}]},
            )

        await ollama_provider._client._client.aclose()
        ollama_provider._client._client = _mock_client(handler)
        info = await ollama_provider.provider_info()
        assert info.name == "ollama"
        assert info.display_name == "Ollama"
        assert info.is_available is True
        assert info.supports_streaming is True


# ── Fallback Tests ──


class TestFallback:
    async def test_fallback_on_primary_failure(self, service_with_fallback: AIService):
        def or_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(502)

        def ollama_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "model": "llama3",
                    "message": {"content": "Fallback response"},
                    "done": True,
                    "done_reason": "stop",
                },
            )

        or_provider = service_with_fallback._registry.resolve("openrouter")
        await or_provider._client._client.aclose()
        or_provider._client._client = _mock_client(or_handler)

        ollama_prov = service_with_fallback._registry.resolve("ollama")
        await ollama_prov._client._client.aclose()
        ollama_prov._client._client = _mock_client(ollama_handler)

        response = await service_with_fallback.generate(AIRequest(prompt="Test"))
        assert response.content == "Fallback response"
        assert response.provider == "ollama"

    async def test_no_fallback_on_success(self, service_with_fallback: AIService):
        def or_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "id": "gen-1",
                    "model": "gpt-4o",
                    "choices": [{"message": {"content": "Primary success"}, "finish_reason": "stop"}],
                },
            )

        or_provider = service_with_fallback._registry.resolve("openrouter")
        await or_provider._client._client.aclose()
        or_provider._client._client = _mock_client(or_handler)

        response = await service_with_fallback.generate(AIRequest(prompt="Test"))
        assert response.content == "Primary success"
        assert response.provider == "openrouter"

    async def test_fallback_not_used_for_empty_prompt(self, service_with_fallback: AIService):
        with pytest.raises(Exception):
            await service_with_fallback.generate(AIRequest(prompt="   "))

    async def test_nonexistent_provider_raises(self, service_openrouter: AIService):
        with pytest.raises(ProviderNotFoundError):
            await service_openrouter.generate(AIRequest(prompt="Test", provider="nonexistent"))

    async def test_both_providers_fail_raises_last_error(self, service_with_fallback: AIService):
        def fail_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(502)

        for name in ["openrouter", "ollama"]:
            prov = service_with_fallback._registry.resolve(name)
            await prov._client._client.aclose()
            prov._client._client = _mock_client(fail_handler)

        with pytest.raises(ProviderUnavailableError):
            await service_with_fallback.generate(AIRequest(prompt="Test"))

    async def test_no_fallback_provider_configured(self, service_openrouter: AIService):
        def or_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "id": "gen-1",
                    "model": "gpt-4o",
                    "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
                },
            )

        or_provider = service_openrouter._registry.resolve("openrouter")
        await or_provider._client._client.aclose()
        or_provider._client._client = _mock_client(or_handler)

        response = await service_openrouter.generate(AIRequest(prompt="Test"))
        assert response.content == "OK"


# ── Provider Factory Tests ──


class TestProviderFactory:
    async def test_factory_registers_providers(self):
        from app.ai.factory import AIProviderFactory

        config = AIConfig(
            default_provider="openrouter",
            enabled_providers=["openrouter", "ollama"],
            openrouter_api_key="sk-test",
        )
        registry = AIProviderRegistry()
        factory = AIProviderFactory(registry, config)
        factory.register_all()
        assert registry.is_registered("openrouter")
        assert registry.is_registered("ollama")
        assert registry.count() == 2

    async def test_factory_skips_disabled_providers(self):
        from app.ai.factory import AIProviderFactory

        config = AIConfig(
            default_provider="openrouter",
            enabled_providers=["openrouter"],
            openrouter_api_key="sk-test",
        )
        registry = AIProviderRegistry()
        factory = AIProviderFactory(registry, config)
        factory.register_all()
        assert registry.is_registered("openrouter")
        assert not registry.is_registered("ollama")

    async def test_factory_warns_for_unknown_providers(self):
        from app.ai.factory import AIProviderFactory

        config = AIConfig(
            enabled_providers=["openrouter", "unknown_provider"],
            openrouter_api_key="sk-test",
        )
        registry = AIProviderRegistry()
        factory = AIProviderFactory(registry, config)
        factory.register_all()
        assert registry.is_registered("openrouter")
        assert registry.count() == 1

    async def test_factory_does_not_register_not_implemented(self):
        from app.ai.factory import AIProviderFactory

        config = AIConfig(
            enabled_providers=["openai", "anthropic", "gemini"],
        )
        registry = AIProviderRegistry()
        factory = AIProviderFactory(registry, config)
        factory.register_all()
        assert registry.is_registered("openai")
        assert registry.is_registered("anthropic")
        assert registry.is_registered("gemini")
        assert registry.count() == 3

    async def test_factory_normalizes_names(self):
        from app.ai.factory import AIProviderFactory

        config = AIConfig(
            enabled_providers=["OpenRouter", "OLLAMA", "  openai  "],
            openrouter_api_key="sk-test",
        )
        registry = AIProviderRegistry()
        factory = AIProviderFactory(registry, config)
        factory.register_all()
        assert registry.is_registered("openrouter")
        assert registry.is_registered("ollama")
        assert registry.is_registered("openai")
        assert registry.count() == 3
