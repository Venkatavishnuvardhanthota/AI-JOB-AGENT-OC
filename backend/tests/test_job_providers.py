from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.jobs.config import AdzunaConfig, JobDiscoveryConfig
from app.jobs.exceptions import ProviderUnavailableError
from app.jobs.http_client import JobHTTPClient
from app.jobs.providers.adzuna import AdzunaJobProvider
from app.jobs.providers.mock import MockJobProvider
from app.jobs.rate_limiter import TokenBucketRateLimiter
from app.jobs.schemas import (
    EmploymentType,
    ExperienceLevel,
    JobProviderInfo,
    JobSearchRequest,
    RemoteType,
)


class TestTokenBucketRateLimiter:
    def test_initial_tokens(self):
        limiter = TokenBucketRateLimiter(rate=10, burst=5)
        assert limiter._tokens == 5.0
        assert limiter._rate == 10.0
        assert limiter._burst == 5

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            TokenBucketRateLimiter(rate=-1, burst=5)

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError):
            TokenBucketRateLimiter(rate=0, burst=5)

    def test_below_min_burst_raises(self):
        with pytest.raises(ValueError):
            TokenBucketRateLimiter(rate=10, burst=0)

    def test_acquire_reduces_tokens(self):
        limiter = TokenBucketRateLimiter(rate=100, burst=10)
        initial = limiter._tokens
        import asyncio

        asyncio.run(limiter.acquire())
        assert limiter._tokens < initial

    def test_refill_increases_tokens(self):
        limiter = TokenBucketRateLimiter(rate=100, burst=10)
        limiter._tokens = 0
        limiter._last_refill = 0
        limiter._refill()
        assert limiter._tokens > 0

    async def test_concurrent_acquire_rate_limits(self):
        limiter = TokenBucketRateLimiter(rate=1, burst=1)
        acquired = [False] * 5

        async def acquire(idx):
            await limiter.acquire()
            acquired[idx] = True

        import asyncio

        tasks = [asyncio.create_task(acquire(i)) for i in range(5)]
        await asyncio.sleep(0.05)
        count_early = sum(acquired)
        await asyncio.sleep(5.0)
        count_later = sum(acquired)
        for t in tasks:
            t.cancel()
        assert count_early <= 2, f"Expected <=2 acquires early, got {count_early}"
        assert count_later >= 3, f"Expected >=3 acquires later, got {count_later}"


class TestJobHTTPClient:
    @pytest.fixture
    def mock_response(self):
        mr = MagicMock(spec=httpx.Response)
        mr.status_code = 200
        mr.json.return_value = {"results": [], "count": 0}
        mr.headers = {}
        return mr

    @pytest.fixture
    def client(self):
        return JobHTTPClient(
            base_url="https://test.example.com",
            timeout_seconds=10,
            max_retries=1,
        )

    async def test_get_success(self, client, mock_response):
        with patch.object(client._client, "get", AsyncMock(return_value=mock_response)):
            result = await client.get("/test")
            assert result == {"results": [], "count": 0}

    async def test_get_retry_on_500(self):
        client = JobHTTPClient(base_url="https://test.example.com", max_retries=2)
        fail_resp = MagicMock(spec=httpx.Response)
        fail_resp.status_code = 500
        fail_resp.text = "error"
        fail_resp.headers = {}
        success_resp = MagicMock(spec=httpx.Response)
        success_resp.status_code = 200
        success_resp.json.return_value = {"ok": True}
        success_resp.headers = {}
        mock_get = AsyncMock(side_effect=[fail_resp, success_resp])
        with patch.object(client._client, "get", mock_get):
            result = await client.get("/test")
            assert result == {"ok": True}

    async def test_get_401_raises(self, client):
        err_resp = MagicMock(spec=httpx.Response)
        err_resp.status_code = 401
        err_resp.headers = {}
        patch_get = patch.object(client._client, "get", AsyncMock(return_value=err_resp))
        with patch_get, pytest.raises(ProviderUnavailableError, match="Authentication failed"):
            await client.get("/test")

    async def test_get_timeout_raises(self, client):
        patch_get = patch.object(client._client, "get", AsyncMock(side_effect=httpx.TimeoutException("timeout")))
        with patch_get, pytest.raises(ProviderUnavailableError, match="timed out"):
            await client.get("/test")

    async def test_get_connect_error_raises(self, client):
        patch_get = patch.object(client._client, "get", AsyncMock(side_effect=httpx.ConnectError("refused")))
        with patch_get, pytest.raises(ProviderUnavailableError, match="Connection failed"):
            await client.get("/test")

    async def test_retry_after_header(self):
        client = JobHTTPClient(base_url="https://test.example.com", max_retries=2)
        resp_429 = MagicMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.text = "rate limited"
        resp_429.headers = {"Retry-After": "0.01"}
        resp_200 = MagicMock(spec=httpx.Response)
        resp_200.status_code = 200
        resp_200.json.return_value = {"ok": True}
        resp_200.headers = {}
        responses = [resp_429, resp_200]
        mock_get = AsyncMock(side_effect=lambda *a, **kw: responses.pop(0))
        with patch.object(client._client, "get", mock_get):
            result = await client.get("/test")
            assert result == {"ok": True}
        await client.close()

    async def test_async_context_manager(self):
        client = JobHTTPClient(base_url="https://test.com")
        mock_close = AsyncMock()
        client.close = mock_close
        async with client as c:
            assert c is client
        mock_close.assert_awaited_once()

    async def test_rate_limited_request(self):
        limiter = TokenBucketRateLimiter(rate=1000, burst=100)
        client = JobHTTPClient(
            base_url="https://test.com",
            rate_limiter=limiter,
        )
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}
        mock_resp.headers = {}
        with patch.object(client._client, "get", AsyncMock(return_value=mock_resp)):
            result = await client.get("/test")
            assert result == {"ok": True}


class TestBaseJobProvider:
    def test_default_attributes(self):
        config = JobDiscoveryConfig()
        provider = MockJobProvider(config)
        assert provider.name == "mock"
        assert provider.display_name == "Mock Provider"
        assert provider.supports_pagination is True

    async def test_provider_info(self):
        config = JobDiscoveryConfig()
        provider = MockJobProvider(config)
        info = await provider.provider_info()
        assert info.name == "mock"
        assert info.is_available is True
        assert isinstance(info, JobProviderInfo)

    async def test_health_check(self):
        config = JobDiscoveryConfig()
        provider = MockJobProvider(config)
        result = await provider.health_check()
        assert result is True


class TestAdzunaJobProvider:
    @pytest.fixture
    def config(self):
        return JobDiscoveryConfig(
            enabled_providers=["adzuna"],
            adzuna=AdzunaConfig(
                app_id="test-id",
                api_key="test-key",
                base_url="https://api.adzuna.com/v1/api/jobs",
            ),
        )

    @pytest.fixture
    def provider(self, config):
        return AdzunaJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "adzuna"
        assert provider.display_name == "Adzuna"
        assert provider.supports_pagination is True
        assert provider.supports_filters is True

    def test_default_params(self, provider):
        params = provider._default_query_params()
        assert params["app_id"] == "test-id"
        assert params["app_key"] == "test-key"

    def test_build_search_params_query(self, provider):
        request = JobSearchRequest(query="python developer", location="New York")
        params = provider._build_search_params(request)
        assert params["what"] == "python developer"
        assert params["where"] == "New York"
        assert params["results_per_page"] == 25

    def test_build_search_params_remote(self, provider):
        request = JobSearchRequest(query="engineer", remote_only=True)
        params = provider._build_search_params(request)
        assert params["remote"] == 1

    def test_build_search_params_salary(self, provider):
        request = JobSearchRequest(query="engineer", salary_min=50000, salary_max=150000)
        params = provider._build_search_params(request)
        assert params["salary_min"] == 50000
        assert params["salary_max"] == 150000

    def test_build_search_params_posted_within(self, provider):
        request = JobSearchRequest(query="engineer", posted_within_days=7)
        params = provider._build_search_params(request)
        assert params["max_days_old"] == 7

    def test_build_search_params_employment_type(self, provider):
        request = JobSearchRequest(query="engineer", employment_type=EmploymentType.FULL_TIME)
        params = provider._build_search_params(request)
        assert params["contract_type"] == "permanent"

    def test_build_search_params_with_keywords(self, provider):
        request = JobSearchRequest(keywords=["python", "django"])
        params = provider._build_search_params(request)
        assert params["what"] == "python django"

    def test_parse_response(self, provider):
        data = {
            "count": 2,
            "results": [
                {
                    "id": "123",
                    "title": "Python Developer",
                    "company": {"display_name": "Tech Corp"},
                    "location": {"display_name": "San Francisco, CA, US"},
                    "description": "Build APIs",
                    "redirect_url": "https://example.com/job/123",
                    "salary_min": 100000,
                    "salary_max": 150000,
                    "salary_currency": "USD",
                    "contract_type": "permanent",
                    "contract_time": "full_time",
                    "created": "2024-01-15T00:00:00Z",
                },
            ],
        }
        request = JobSearchRequest(query="python")
        response = provider._parse_response(data, request)
        assert len(response.results) == 1
        assert response.metadata.total_results == 2
        assert response.results[0].title == "Python Developer"
        assert response.results[0].company.name == "Tech Corp"

    def test_parse_response_empty(self, provider):
        data = {"count": 0, "results": []}
        request = JobSearchRequest(query="nothing")
        response = provider._parse_response(data, request)
        assert len(response.results) == 0
        assert response.metadata.total_results == 0

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "abc-123",
            "title": "Senior Software Engineer",
            "company": {"display_name": "Acme Inc"},
            "location": {"display_name": "Seattle, WA, US"},
            "description": "Build and ship features.",
            "redirect_url": "https://acme.com/jobs/sse",
            "salary_min": 120000,
            "salary_max": 180000,
            "salary_currency": "USD",
            "contract_type": "permanent",
            "contract_time": "full_time",
            "created": "2024-03-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "abc-123"
        assert posting.title == "Senior Software Engineer"
        assert posting.company.name == "Acme Inc"
        assert posting.location.city == "Seattle"
        assert posting.location.country == "US"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.salary is not None
        assert posting.salary.min_amount == 120000
        assert posting.salary.max_amount == 180000
        assert posting.salary.currency == "USD"

    def test_raw_to_posting_minimal(self, provider):
        raw = {"id": "1", "title": "Dev", "company": {}, "location": {}}
        posting = provider._raw_to_posting(raw)
        assert posting.title == "Dev"
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_parse_location_full(self, provider):
        loc = provider._parse_location("San Francisco, CA, US", {})
        assert loc.city == "San Francisco"
        assert loc.state == "CA"
        assert loc.country == "US"
        assert loc.remote_type == RemoteType.ON_SITE

    def test_parse_location_two_parts(self, provider):
        loc = provider._parse_location("Toronto, ON", {})
        assert loc.city == "Toronto"
        assert loc.state == "ON"
        assert loc.country is None

    def test_parse_location_remote_flag(self, provider):
        loc = provider._parse_location("Remote, US", {"remote": True})
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salary_min": 50000, "salary_max": 100000, "salary_currency": "EUR"})
        assert sal is not None
        assert sal.min_amount == 50000
        assert sal.max_amount == 100000
        assert sal.currency == "EUR"

    def test_parse_salary_none(self, provider):
        sal = provider._parse_salary({})
        assert sal is None

    def test_parse_salary_predicted(self, provider):
        sal = provider._parse_salary({"salary_min": 60000, "salary_is_predicted": True})
        assert sal is not None
        assert sal.interval == "predicted"

    def test_normalize_experience_senior(self, provider):
        assert provider._normalize_experience("Senior Engineer", {}) == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Lead Developer", {}) == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Principal Architect", {}) == ExperienceLevel.SENIOR

    def test_normalize_experience_junior(self, provider):
        assert provider._normalize_experience("Junior Developer", {}) == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Jr. Engineer", {}) == ExperienceLevel.JUNIOR

    def test_normalize_experience_executive(self, provider):
        assert provider._normalize_experience("Director of Engineering", {}) == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("VP of Product", {}) == ExperienceLevel.EXECUTIVE

    def test_normalize_experience_entry(self, provider):
        assert provider._normalize_experience("Intern", {}) == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Trainee", {}) == ExperienceLevel.ENTRY

    def test_normalize_experience_default_mid(self, provider):
        assert provider._normalize_experience("Software Engineer", {}) == ExperienceLevel.MID
        assert provider._normalize_experience("Data Analyst", {}) == ExperienceLevel.MID

    def test_adzuna_contract_type(self, provider):
        assert provider._adzuna_contract_type(EmploymentType.FULL_TIME) == "permanent"
        assert provider._adzuna_contract_type(EmploymentType.CONTRACT) == "contract"
        assert provider._adzuna_contract_type(None) is None

    async def test_search_jobs_integration(self, provider):
        mock_data = {
            "count": 1,
            "results": [
                {
                    "id": "1",
                    "title": "Python Developer",
                    "company": {"display_name": "Co"},
                    "location": {"display_name": "NYC"},
                    "description": "desc",
                    "redirect_url": "https://example.com/job",
                    "salary_min": 80000,
                    "salary_max": 120000,
                    "salary_currency": "USD",
                    "created": "2024-01-01T00:00:00Z",
                },
            ],
        }
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            request = JobSearchRequest(query="python")
            response = await provider.search_jobs(request)
            assert len(response.results) == 1
            assert response.results[0].title == "Python Developer"

    async def test_health_check_success(self, provider):
        mock_data = {"count": 0, "results": []}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            result = await provider.health_check()
            assert result is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            result = await provider.health_check()
            assert result is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"count": 0, "results": []})):
            info = await provider.provider_info()
            assert info.name == "adzuna"
            assert info.is_available is True

    def test_page_limit(self, provider):
        request = JobSearchRequest(query="test", limit=50)
        assert provider._page_limit(request) == 25

    def test_page_limit_default(self, provider):
        request = JobSearchRequest(query="test")
        assert provider._page_limit(request) == 25

    def test_page_offset(self, provider):
        request = JobSearchRequest(query="test", offset=20)
        assert provider._page_offset(request) == 20


class TestAdzunaProviderEdgeCases:
    @pytest.fixture
    def config(self):
        return JobDiscoveryConfig(
            enabled_providers=["adzuna"],
            adzuna=AdzunaConfig(app_id="id", api_key="key"),
        )

    @pytest.fixture
    def provider(self, config):
        return AdzunaJobProvider(config)

    def test_empty_company_data(self, provider):
        raw = {"id": "1", "title": "Dev", "company": None, "location": None}
        posting = provider._raw_to_posting(raw)
        assert posting.company.name == "Unknown Company"
        assert posting.location.display_name == ""

    def test_partial_location(self, provider):
        loc = provider._parse_location("London", {})
        assert loc.city == "London"
        assert loc.state is None
        assert loc.country is None

    def test_two_part_location(self, provider):
        loc = provider._parse_location("Toronto, ON", {})
        assert loc.city == "Toronto"
        assert loc.state == "ON"
        assert loc.country is None

    def test_salary_min_only(self, provider):
        sal = provider._parse_salary({"salary_min": 30000})
        assert sal is not None
        assert sal.min_amount == 30000
        assert sal.max_amount is None

    def test_salary_max_only(self, provider):
        sal = provider._parse_salary({"salary_max": 200000})
        assert sal is not None
        assert sal.min_amount is None
        assert sal.max_amount == 200000


class TestJobProviderFactory:
    def test_register_mock_always(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = JobDiscoveryConfig()
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        register_call_names = [call[0][0].name for call in registry.register.call_args_list]
        assert "mock" in register_call_names

    def test_register_adzuna_when_configured(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = JobDiscoveryConfig(
            enabled_providers=["adzuna"],
            adzuna=AdzunaConfig(app_id="id", api_key="key"),
        )
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        register_call_names = [call[0][0].name for call in registry.register.call_args_list]
        assert "adzuna" in register_call_names

    def test_skip_adzuna_when_not_configured(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = JobDiscoveryConfig(enabled_providers=["adzuna"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        register_call_names = [call[0][0].name for call in registry.register.call_args_list]
        assert "adzuna" not in register_call_names

    def test_skip_already_registered(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = True
        config = JobDiscoveryConfig()
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        registry.register.assert_not_called()


class TestConfig:
    def test_adzuna_config_defaults(self):
        config = AdzunaConfig()
        assert config.app_id == ""
        assert config.api_key == ""
        assert config.base_url == "https://api.adzuna.com/v1/api/jobs"
        assert config.page_size == 20
        assert config.rate_limit_rate == 5.0
        assert config.rate_limit_burst == 3

    def test_job_discovery_config_with_adzuna(self):
        config = JobDiscoveryConfig(
            enabled_providers=["adzuna"],
            adzuna=AdzunaConfig(app_id="test-id", api_key="test-key"),
        )
        assert config.adzuna.app_id == "test-id"
        assert config.adzuna.api_key == "test-key"

    def test_adzuna_page_size_validation(self):
        with pytest.raises(Exception):
            AdzunaConfig(page_size=0)
        with pytest.raises(Exception):
            AdzunaConfig(page_size=100)
