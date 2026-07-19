"""Tests for the Phase 7 LLM abstraction, embeddings, vector store, RAG, and prompts."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.llm import (
    EmbeddingResponse,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    PromptRenderRequest,
    PromptRenderResponse,
    PromptTemplateCreate,
    RAGRequest,
    VectorDocument,
    VectorSearchRequest,
)
from app.services.llm.cache import LLMCache
from app.services.llm.config import LLMProviderItem, llm_config
from app.services.llm.embeddings import EmbeddingService
from app.services.llm.factory import get_llm_client, list_providers
from app.services.llm.prompts.registry import PromptRegistry
from app.services.llm.prompts.templates import PromptTemplateService
from app.services.llm.rag import RAGService
from app.services.llm.vector_store import VectorStore, cosine_similarity

# ── LLM Config ──


class TestLLMConfig:
    def test_default_config(self):
        assert llm_config.default_provider == "openai"
        assert llm_config.embedding_dimension == 1536

    def test_providers_configured(self):
        assert "openai" in llm_config.providers
        assert "ollama" in llm_config.providers
        assert llm_config.providers["ollama"].base_url == "http://localhost:11434"

    def test_llm_provider_item_defaults(self):
        item = LLMProviderItem(provider="test", default_model="m")
        assert item.timeout == 60
        assert item.max_retries == 3
        assert item.enabled is True


# ── LLM Cache ──


class TestLLMCache:
    def test_cache_miss(self):
        cache = LLMCache(ttl_seconds=3600)
        req = LLMRequest(messages=[LLMMessage(role="user", content="hi")])
        assert cache.get(req) is None

    def test_cache_hit(self):
        cache = LLMCache(ttl_seconds=3600)
        req = LLMRequest(messages=[LLMMessage(role="user", content="hi")])
        resp = LLMResponse(content="hello", model="gpt-4o", provider="openai")
        cache.set(req, resp)
        cached = cache.get(req)
        assert cached is not None
        assert cached.content == "hello"

    def test_cache_eviction(self):
        cache = LLMCache(ttl_seconds=3600, max_size=2)
        req1 = LLMRequest(messages=[LLMMessage(role="user", content="a")])
        req2 = LLMRequest(messages=[LLMMessage(role="user", content="b")])
        req3 = LLMRequest(messages=[LLMMessage(role="user", content="c")])
        resp = LLMResponse(content="x", model="m", provider="p")
        cache.set(req1, resp)
        cache.set(req2, resp)
        cache.set(req3, resp)
        assert cache.get(req1) is None
        assert cache.get(req3) is not None

    def test_cache_invalidate(self):
        cache = LLMCache()
        req = LLMRequest(messages=[LLMMessage(role="user", content="hi")])
        resp = LLMResponse(content="hello", model="m", provider="p")
        cache.set(req, resp)
        cache.invalidate(req)
        assert cache.get(req) is None

    def test_cache_clear(self):
        cache = LLMCache()
        req = LLMRequest(messages=[LLMMessage(role="user", content="hi")])
        cache.set(req, LLMResponse(content="x", model="m", provider="p"))
        cache.clear()
        assert cache.size == 0

    def test_cache_different_requests_different_keys(self):
        cache = LLMCache()
        req1 = LLMRequest(messages=[LLMMessage(role="user", content="hi")])
        req2 = LLMRequest(messages=[LLMMessage(role="user", content="bye")])
        resp = LLMResponse(content="x", model="m", provider="p")
        cache.set(req1, resp)
        assert cache.get(req2) is None

    def test_cache_ttl_expiry(self):
        cache = LLMCache(ttl_seconds=0)
        req = LLMRequest(messages=[LLMMessage(role="user", content="hi")])
        resp = LLMResponse(content="x", model="m", provider="p")
        cache.set(req, resp)
        with patch("app.services.llm.cache.time.monotonic", return_value=999999):
            assert cache.get(req) is None


# ── Vector Store ──


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_empty_vector(self):
        assert cosine_similarity([], [1, 2]) == 0.0
        assert cosine_similarity([1, 2], []) == 0.0

    def test_partial_match(self):
        sim = cosine_similarity([1, 2, 3], [1, 2, 0])
        assert 0.5 < sim < 1.0


class TestVectorStore:
    def test_add_and_search(self):
        store = VectorStore()
        store.add_document("doc1", "Python developer", [1.0, 0.0, 0.0])
        store.add_document("doc2", "Java developer", [0.0, 1.0, 0.0])
        results = store.search([1.0, 0.0, 0.0], top_k=5, min_score=0.0)
        assert len(results) == 2
        assert results[0].id == "doc1"

    def test_search_with_min_score(self):
        store = VectorStore()
        store.add_document("doc1", "Python", [1.0, 0.0])
        store.add_document("doc2", "Java", [0.0, 1.0])
        results = store.search([1.0, 0.0], top_k=5, min_score=0.5)
        assert len(results) == 1
        assert results[0].id == "doc1"

    def test_remove_document(self):
        store = VectorStore()
        store.add_document("doc1", "Python", [1.0, 0.0])
        assert store.size == 1
        store.remove_document("doc1")
        assert store.size == 0

    def test_clear(self):
        store = VectorStore()
        store.add_document("doc1", "Python", [1.0, 0.0])
        store.add_document("doc2", "Java", [0.0, 1.0])
        store.clear()
        assert store.size == 0

    def test_search_empty_store(self):
        store = VectorStore()
        results = store.search([1.0, 0.0], top_k=5)
        assert results == []

    def test_search_returns_score(self):
        store = VectorStore()
        store.add_document("doc1", "Python", [1.0, 0.0])
        results = store.search([1.0, 0.0], top_k=5)
        assert results[0].score is not None
        assert results[0].score == pytest.approx(1.0, abs=0.01)

    def test_search_with_metadata(self):
        store = VectorStore()
        store.add_document("doc1", "Python", [1.0, 0.0], {"source": "job"})
        results = store.search([1.0, 0.0], top_k=5)
        assert results[0].metadata == {"source": "job"}


# ── Embedding Service ──


class TestEmbeddingService:
    @pytest.mark.asyncio
    async def test_embed_openai(self):
        svc = EmbeddingService(provider="openai", api_key="test-key")
        mock_resp = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}, {"embedding": [0.4, 0.5, 0.6]}],
            "model": "text-embedding-3-small",
        }
        with patch.object(svc._client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=lambda: None,
                json=lambda: mock_resp,
            )
            result = await svc.embed(["hello", "world"])
        assert isinstance(result, EmbeddingResponse)
        assert len(result.embeddings) == 2
        assert result.dimension == 3
        assert result.provider == "openai"

    @pytest.mark.asyncio
    async def test_embed_ollama(self):
        svc = EmbeddingService(provider="ollama", base_url="http://localhost:11434")
        mock_resp = {
            "embeddings": [[0.1, 0.2], [0.3, 0.4]],
            "model": "llama3.2",
        }
        with patch.object(svc._client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=lambda: None,
                json=lambda: mock_resp,
            )
            result = await svc.embed(["hello"])
        assert len(result.embeddings) == 2
        assert result.provider == "ollama"

    @pytest.mark.asyncio
    async def test_embed_gemini(self):
        svc = EmbeddingService(provider="gemini", api_key="test-key")
        mock_resp = {
            "embeddings": [{"values": [0.1, 0.2]}, {"values": [0.3, 0.4]}],
        }
        with patch.object(svc._client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=lambda: None,
                json=lambda: mock_resp,
            )
            result = await svc.embed(["hello"])
        assert len(result.embeddings) == 2

    @pytest.mark.asyncio
    async def test_embed_unsupported_provider(self):
        svc = EmbeddingService(provider="unsupported")
        with pytest.raises(ValueError, match="not supported"):
            await svc.embed(["hello"])


# ── RAG Service ──


class TestRAGService:
    @pytest.mark.asyncio
    async def test_query_with_results(self):
        store = VectorStore()
        store.add_document("doc1", "Python is a programming language.", [1.0, 0.0])
        store.add_document("doc2", "Java is also a language.", [0.0, 1.0])
        emb_svc = MagicMock()
        emb_svc.embed = AsyncMock(
            return_value=EmbeddingResponse(
                embeddings=[[1.0, 0.0]],
                model="test",
                provider="test",
                dimension=2,
            )
        )
        rag = RAGService(vector_store=store, embedding_service=emb_svc)
        with patch("app.services.llm.rag.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.complete = AsyncMock(
                return_value=LLMResponse(
                    content="Test answer",
                    model="test",
                    provider="test",
                )
            )
            mock_get.return_value = mock_client
            result = await rag.query(RAGRequest(query="Tell me about Python"))
        assert "Test answer" in result.answer
        assert len(result.sources) > 0

    @pytest.mark.asyncio
    async def test_query_no_llm_client(self):
        store = VectorStore()
        emb_svc = MagicMock()
        emb_svc.embed = AsyncMock(
            return_value=EmbeddingResponse(
                embeddings=[[0.1, 0.2]],
                model="test",
                provider="test",
                dimension=2,
            )
        )
        rag = RAGService(vector_store=store, embedding_service=emb_svc)
        with patch("app.services.llm.rag.get_llm_client") as mock_get:
            mock_get.return_value = None
            result = await rag.query(RAGRequest(query="hello"))
        assert "No LLM client available" in result.answer

    @pytest.mark.asyncio
    async def test_empty_vector_store(self):
        store = VectorStore()
        emb_svc = MagicMock()
        emb_svc.embed = AsyncMock(
            return_value=EmbeddingResponse(
                embeddings=[[0.1, 0.2]],
                model="test",
                provider="test",
                dimension=2,
            )
        )
        rag = RAGService(vector_store=store, embedding_service=emb_svc)
        with patch("app.services.llm.rag.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.complete = AsyncMock(
                return_value=LLMResponse(content="No context found", model="t", provider="t")
            )
            mock_get.return_value = mock_client
            result = await rag.query(RAGRequest(query="hello"))
        assert len(result.sources) == 0


# ── Prompt Registry ──


class TestPromptRegistry:
    def test_get_built_in_prompt(self):
        registry = PromptRegistry()
        prompt = registry.get_prompt("job-application-email")
        assert prompt is not None
        assert prompt["version"] == 1

    def test_get_nonexistent_prompt(self):
        registry = PromptRegistry()
        assert registry.get_prompt("nonexistent") is None

    def test_get_specific_version(self):
        registry = PromptRegistry()
        prompt = registry.get_prompt("job-application-email", version=1)
        assert prompt is not None

    def test_get_nonexistent_version(self):
        registry = PromptRegistry()
        assert registry.get_prompt("job-application-email", version=99) is None

    def test_list_prompts(self):
        registry = PromptRegistry()
        prompts = registry.list_prompts()
        names = [p["name"] for p in prompts]
        assert "job-application-email" in names
        assert "cover-letter" in names
        assert "interview-prep" in names

    def test_register_new_prompt(self):
        registry = PromptRegistry()
        entry = registry.register_prompt(
            name="test-prompt",
            template="Hello {{name}}",
            variables=["name"],
            description="Test",
        )
        assert entry["version"] == 1
        assert registry.get_prompt("test-prompt") is not None

    def test_register_existing_increments_version(self):
        registry = PromptRegistry()
        registry.register_prompt("test-inc", template="v1 {{x}}")
        entry = registry.register_prompt("test-inc", template="v2 {{x}}")
        assert entry["version"] == 2

    def test_render(self):
        registry = PromptRegistry()
        result = registry.render(
            "job-application-email",
            {"job_title": "Engineer", "company_name": "Acme", "applicant_name": "John"},
        )
        assert result is not None
        assert "Engineer" in result.rendered
        assert "Acme" in result.rendered
        assert "John" in result.rendered

    def test_render_nonexistent(self):
        registry = PromptRegistry()
        assert registry.render("nonexistent", {}) is None

    def test_render_with_auto_variables(self):
        registry = PromptRegistry()
        entry = registry.register_prompt("auto-vars", template="{{a}} and {{b}}")
        assert "a" in entry["variables"]
        assert "b" in entry["variables"]


# ── Prompt Template Service ──


class TestPromptTemplateService:
    @pytest.mark.asyncio
    async def test_create_template(self):
        from datetime import datetime, timezone

        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", "mock-id"))

        svc = PromptTemplateService(session)
        from app.schemas.llm import PromptTemplateResponse
        svc._to_response = lambda p: PromptTemplateResponse(
            id=str(p.id) if hasattr(p, "id") else "mock-id",
            name=p.name,
            version=p.version,
            template=p.template,
            variables=p.variables or [],
            description=p.description,
            model=p.model,
            is_active=p.is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = await svc.create(
            PromptTemplateCreate(
                name="test-template",
                template="Hello {{name}}",
                description="Test",
            )
        )
        assert result.name == "test-template"
        assert result.version == 1
        assert "name" in result.variables

    def test_extract_variables(self):
        svc = PromptTemplateService(MagicMock())
        vars_ = svc._extract_variables("Hello {{name}}, your {{role}} is active")
        assert "name" in vars_
        assert "role" in vars_
        assert len(vars_) == 2

    def test_extract_variables_empty(self):
        svc = PromptTemplateService(MagicMock())
        assert svc._extract_variables("No variables here") == []


# ── Factory ──


class TestFactory:
    def test_list_providers(self):
        providers = list_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0

    def test_get_known_provider(self):
        client = get_llm_client("openai")
        if client:
            assert client.provider == "openai"

    def test_get_unknown_provider(self):
        with patch.dict(llm_config.providers, {}, clear=True):
            result = get_llm_client("unknown")
            assert result is None


# ── Schemas ──


class TestLLMSchemas:
    def test_llm_message_validation(self):
        msg = LLMMessage(role="user", content="hello")
        assert msg.role == "user"

    def test_llm_message_invalid_role(self):
        with pytest.raises(ValueError):
            LLMMessage(role="invalid", content="x")

    def test_llm_request_defaults(self):
        req = LLMRequest(messages=[LLMMessage(role="user", content="hi")])
        assert req.stream is False
        assert req.temperature is None

    def test_llm_response(self):
        resp = LLMResponse(content="hello", model="gpt-4o", provider="openai")
        assert resp.content == "hello"
        assert resp.latency_ms is None

    def test_embedding_response(self):
        resp = EmbeddingResponse(
            embeddings=[[0.1, 0.2]],
            model="test",
            provider="test",
            dimension=2,
        )
        assert len(resp.embeddings) == 1

    def test_vector_document_with_score(self):
        doc = VectorDocument(id="1", content="test", score=0.95)
        assert doc.score == 0.95

    def test_vector_search_request(self):
        req = VectorSearchRequest(query="test", top_k=5)
        assert req.top_k == 5
        assert req.min_score == 0.0

    def test_rag_request(self):
        req = RAGRequest(query="test", top_k=3, min_score=0.5)
        assert req.top_k == 3
        assert req.min_score == 0.5

    def test_prompt_render_request(self):
        req = PromptRenderRequest(name="test", variables={"key": "val"})
        assert req.name == "test"
        assert req.variables["key"] == "val"

    def test_prompt_render_response(self):
        resp = PromptRenderResponse(rendered="hello", name="test", version=1)
        assert resp.rendered == "hello"
