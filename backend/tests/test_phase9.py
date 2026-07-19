"""Tests for Phase 9: Company Research Engine with caching and persistence."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.company_research import CompanyResearch
from app.repositories.user import UserRepository
from app.schemas.company_research import (
    CompanyResearchRequest,
    CompanyResearchResponse,
    CompanyResearchSummary,
)
from app.services.company_research import (
    CompanyResearchService,
    _InMemoryCache,
)

# ── Fixtures ──


@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(
        email="phase9_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Phase9 Test User",
    )
    return user


@pytest_asyncio.fixture
async def auth_client(test_user, session: AsyncSession):
    from app.api.deps import get_current_user

    async def override_get_db():
        yield session

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ── Fixtures for sample data ──


@pytest.fixture
def sample_llm_response():
    return {
        "company_name": "Acme Corp",
        "industry": "Technology",
        "mission": "To build innovative software solutions",
        "values": ["Innovation", "Integrity", "Customer Focus"],
        "products_or_services": ["Cloud Platform", "Analytics Tool"],
        "company_culture": "Fast-paced, collaborative environment",
        "recent_news": ["Launched AI product in 2025", "Opened new office in Austin"],
        "headquarters": "San Francisco, CA",
        "company_size": "1000-5000",
        "linkedin_url": "https://linkedin.com/company/acme",
        "hiring_trends": ["Growing engineering team", "Expanding remote workforce"],
        "technology_stack": ["Python", "AWS", "Kubernetes", "React"],
        "funding": {
            "total_funding": "$200M",
            "last_round": "Series C",
            "last_round_date": "2024",
            "investors": ["Sequoia", "a16z"],
        },
    }


@pytest.fixture
def sample_llm_response_no_funding():
    return {
        "company_name": "Bootstrap Inc",
        "industry": "E-commerce",
        "mission": "To simplify online selling",
        "values": ["Simplicity", "Speed"],
        "products_or_services": ["Shop Platform"],
        "company_culture": "Remote-first",
        "recent_news": ["Reached 1M users"],
        "headquarters": "Austin, TX",
        "company_size": "50-200",
        "linkedin_url": None,
        "hiring_trends": ["Hiring customer support"],
        "technology_stack": ["Ruby on Rails", "PostgreSQL"],
        "funding": None,
    }


def make_mock_llm_client(response_content: str | dict):
    if isinstance(response_content, dict):
        response_content = json.dumps(response_content)
    mock_response = MagicMock()
    mock_response.content = response_content
    mock_client = MagicMock()
    mock_client.complete = AsyncMock(return_value=mock_response)
    return mock_client


def make_fresh_service(session=None):
    return CompanyResearchService(session=session, cache=_InMemoryCache())


# ── Schema Tests ──


class TestCompanyResearchSchemas:
    def test_request_valid(self):
        req = CompanyResearchRequest(company_name="Acme Corp")
        assert req.company_name == "Acme Corp"

    def test_request_empty_raises(self):
        with pytest.raises(ValueError):
            CompanyResearchRequest()

    def test_response_from_attrs(self):
        uid = uuid.uuid4()
        data = {
            "id": uid,
            "company_name": "Acme",
            "industry": "Tech",
            "values": ["Innovation"],
            "products_or_services": ["Software"],
            "recent_news": ["News"],
            "hiring_trends": ["Growing"],
            "technology_stack": ["Python"],
            "funding": {"total_funding": "$100M"},
            "summary": "A tech company.",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        resp = CompanyResearchResponse(**data)
        assert resp.company_name == "Acme"
        assert resp.funding == {"total_funding": "$100M"}

    def test_summary_schema(self):
        s = CompanyResearchSummary(company_name="Acme", summary="A great company.")
        assert s.company_name == "Acme"
        assert s.summary == "A great company."


# ── Service Tests ──


class TestCompanyResearchService:
    @pytest.mark.asyncio
    async def test_research_with_llm(self, sample_llm_response):
        svc = make_fresh_service()
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            result = await svc.research("UniqueCorp")

        assert result["company_name"] == "UniqueCorp"
        assert result["industry"] == "Technology"
        assert "Innovation" in result["values"]
        assert "Cloud Platform" in result["products_or_services"]
        assert result["hiring_trends"] == [
            "Growing engineering team",
            "Expanding remote workforce",
        ]
        assert "Python" in result["technology_stack"]
        assert result["funding"]["total_funding"] == "$200M"
        assert result["summary"] is not None
        assert "UniqueCorp" in result["summary"]
        assert "Technology" in result["summary"]

    @pytest.mark.asyncio
    async def test_research_with_llm_no_funding(self, sample_llm_response_no_funding):
        svc = make_fresh_service()
        mock_client = make_mock_llm_client(sample_llm_response_no_funding)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            result = await svc.research("UniqueBootstrap")

        assert result["company_name"] == "UniqueBootstrap"
        assert result["funding"] is None
        assert result["summary"] is not None

    @pytest.mark.asyncio
    async def test_research_no_llm(self):
        svc = make_fresh_service()
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=None,
        ):
            result = await svc.research("UniqueUnknown")

        assert result["company_name"] == "UniqueUnknown"
        assert result["industry"] is None
        assert result["hiring_trends"] == []
        assert result["technology_stack"] == []
        assert result["funding"] is None
        assert "no detailed information" in result["summary"]

    @pytest.mark.asyncio
    async def test_research_llm_fails(self):
        svc = make_fresh_service()
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(
            side_effect=Exception("LLM unavailable")
        )
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            result = await svc.research("UniqueFails")

        assert result["company_name"] == "UniqueFails"
        assert result["industry"] is None

    @pytest.mark.asyncio
    async def test_research_bad_json(self):
        svc = make_fresh_service()
        mock_client = make_mock_llm_client("this is not json")
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            result = await svc.research("UniqueBadJson")

        assert result["company_name"] == "UniqueBadJson"
        assert result["industry"] is None

    @pytest.mark.asyncio
    async def test_memory_cache_hit(self, sample_llm_response):
        svc = make_fresh_service()
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            result1 = await svc.research("UniqueCacheHit")
            assert result1["industry"] == "Technology"

            result2 = await svc.research("UniqueCacheHit")

        assert result2 is result1

    @pytest.mark.asyncio
    async def test_get_cached_memory(self, sample_llm_response):
        svc = make_fresh_service()
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            await svc.research("UniqueCachedGet")
            cached = await svc.get_cached("UniqueCachedGet")

        assert cached is not None
        assert cached["company_name"] == "UniqueCachedGet"

    @pytest.mark.asyncio
    async def test_get_cached_not_found(self):
        svc = make_fresh_service()
        cached = await svc.get_cached("UniqueNoSuch")
        assert cached is None

    @pytest.mark.asyncio
    async def test_get_summary(self, sample_llm_response):
        svc = make_fresh_service()
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            summary = await svc.get_summary("UniqueSummary")

        assert summary is not None
        assert "UniqueSummary" in summary

    @pytest.mark.asyncio
    async def test_generate_summary_all_fields(self):
        data = {
            "company_name": "TestCorp",
            "industry": "Healthcare",
            "mission": "Heal the world",
            "products_or_services": ["Device A", "Device B", "Service C"],
            "company_culture": "Collaborative",
            "technology_stack": ["Go", "React"],
            "hiring_trends": ["Hiring engineers", "Remote growth"],
            "funding": {"total_funding": "$50M", "last_round": "Series A"},
        }
        summary = CompanyResearchService._generate_summary(data)
        assert "TestCorp" in summary
        assert "Healthcare" in summary
        assert "Device A" in summary
        assert "Go" in summary
        assert "$50M" in summary

    @pytest.mark.asyncio
    async def test_generate_summary_minimal(self):
        data = {"company_name": "MinimalCorp"}
        summary = CompanyResearchService._generate_summary(data)
        assert "MinimalCorp" in summary
        assert "no detailed information" in summary

    @pytest.mark.asyncio
    async def test_invalidate_cache(self):
        svc = make_fresh_service()
        mock_client = make_mock_llm_client(
            {"company_name": "UniqueInv", "industry": "Tech"}
        )
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            await svc.research("UniqueInv")
            assert svc._cache.size == 1
            await svc.invalidate_cache("UniqueInv")
            assert svc._cache.size == 0

    @pytest.mark.asyncio
    async def test_fallback_info(self):
        result = CompanyResearchService._fallback_info("Unknown Corp")
        assert result["company_name"] == "Unknown Corp"
        assert result["hiring_trends"] == []
        assert result["technology_stack"] == []
        assert result["funding"] is None
        assert result["summary"] is not None

    def test_sanitize_result_fills_missing(self):
        result = {"company_name": "Test"}
        sanitized = CompanyResearchService._sanitize_result(result, "Test")
        assert sanitized["company_name"] == "Test"
        assert sanitized["industry"] is None
        assert sanitized["hiring_trends"] == []
        assert sanitized["technology_stack"] == []

    def test_sanitize_result_preserves_values(self):
        result = {
            "company_name": "Test",
            "industry": "Tech",
            "hiring_trends": ["Growing"],
            "technology_stack": ["Python"],
        }
        sanitized = CompanyResearchService._sanitize_result(result, "Test")
        assert sanitized["industry"] == "Tech"
        assert sanitized["hiring_trends"] == ["Growing"]

    @pytest.mark.asyncio
    async def test_db_persistence(self, sample_llm_response):
        mock_session = MagicMock(spec=AsyncSession)

        async def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            return mock_result

        mock_session.execute = AsyncMock(side_effect=mock_execute_side_effect)
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()

        svc = CompanyResearchService(
            session=mock_session, cache=_InMemoryCache()
        )
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            result = await svc.research("UniqueDbPersist")

        assert result["company_name"] == "UniqueDbPersist"
        mock_session.add.assert_called_once()
        args = mock_session.add.call_args[0][0]
        assert isinstance(args, CompanyResearch)
        assert args.company_name == "UniqueDbPersist"

    @pytest.mark.asyncio
    async def test_db_read_on_cache_miss(self):
        mock_model = MagicMock(spec=CompanyResearch)
        mock_model.company_name = "UniqueDbRead"
        mock_model.industry = "Tech"
        mock_model.mission = "Test mission"
        mock_model.values = ["Innovation"]
        mock_model.products_or_services = ["Software"]
        mock_model.company_culture = "Fast"
        mock_model.recent_news = ["News"]
        mock_model.headquarters = "SF"
        mock_model.company_size = "1000"
        mock_model.linkedin_url = None
        mock_model.hiring_trends = ["Growing team"]
        mock_model.technology_stack = ["Python"]
        mock_model.funding = None
        mock_model.summary = "A summary."
        mock_model.cached_at = None

        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        svc = CompanyResearchService(
            session=mock_session, cache=_InMemoryCache()
        )
        cached = await svc.get_cached("UniqueDbRead")
        assert cached is not None
        assert cached["company_name"] == "UniqueDbRead"
        assert cached["hiring_trends"] == ["Growing team"]

    @pytest.mark.asyncio
    async def test_db_write_failure_does_not_crash(self, sample_llm_response):
        mock_session = MagicMock(spec=AsyncSession)

        async def mock_execute_side(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            return mock_result

        mock_session.execute = AsyncMock(side_effect=mock_execute_side)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        svc = CompanyResearchService(
            session=mock_session, cache=_InMemoryCache()
        )
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            result = await svc.research("UniqueDbWriteFail")

        assert result["company_name"] == "UniqueDbWriteFail"
        assert result["industry"] == "Technology"


# ── API Integration Tests ──


class TestPhase9APIIntegration:
    @pytest.mark.asyncio
    async def test_research_company_endpoint(self, auth_client, sample_llm_response):
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            resp = await auth_client.post(
                "/api/v1/company/research",
                json={"company_name": "ApiAcme"},
            )

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["company_name"] == "ApiAcme"
        assert data["industry"] == "Technology"
        assert "Innovation" in data["values"]
        assert data["hiring_trends"] == [
            "Growing engineering team",
            "Expanding remote workforce",
        ]
        assert "Python" in data["technology_stack"]
        assert data["funding"]["total_funding"] == "$200M"
        assert data["summary"] is not None

    @pytest.mark.asyncio
    async def test_get_research_by_name(self, auth_client, sample_llm_response):
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            await auth_client.post(
                "/api/v1/company/research",
                json={"company_name": "ApiGetByName"},
            )
            resp = await auth_client.get(
                "/api/v1/company/research/ApiGetByName",
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["company_name"] == "ApiGetByName"
        assert data["industry"] == "Technology"

    @pytest.mark.asyncio
    async def test_get_research_summary_endpoint(
        self, auth_client, sample_llm_response
    ):
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            await auth_client.post(
                "/api/v1/company/research",
                json={"company_name": "ApiSummary"},
            )
            resp = await auth_client.get(
                "/api/v1/company/research/ApiSummary/summary",
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["company_name"] == "ApiSummary"
        assert data["summary"] is not None

    @pytest.mark.asyncio
    async def test_research_without_auth_returns_401(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/company/research",
                json={"company_name": "NoAuth"},
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_research_auto_triggers(
        self, auth_client, sample_llm_response
    ):
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            resp = await auth_client.get(
                "/api/v1/company/research/ApiAutoTrigger",
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["company_name"] == "ApiAutoTrigger"

    @pytest.mark.asyncio
    async def test_invalidate_cache_endpoint(
        self, auth_client, sample_llm_response
    ):
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            await auth_client.post(
                "/api/v1/company/research",
                json={"company_name": "ApiInvalidate"},
            )
            resp = await auth_client.delete(
                "/api/v1/company/research/ApiInvalidate",
            )

        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_summary_without_prior_research(
        self, auth_client, sample_llm_response
    ):
        mock_client = make_mock_llm_client(sample_llm_response)
        with patch(
            "app.services.company_research.get_llm_client",
            return_value=mock_client,
        ):
            resp = await auth_client.get(
                "/api/v1/company/research/ApiFreshSummary/summary",
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["summary"] is not None
        assert "ApiFreshSummary" in data["summary"]
