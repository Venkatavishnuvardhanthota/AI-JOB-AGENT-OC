"""Unit tests for the provider framework (not platform implementations)."""

from unittest.mock import AsyncMock

import pytest

from app.services.providers.base import BaseProvider, RawJobData
from app.services.providers.config import PROVIDER_CONFIGS, ProviderSettings
from app.services.providers.errors import (
    ProviderAuthError,
    ProviderError,
    ProviderParseError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.services.providers.factory import ProviderFactory, get_provider_factory
from app.services.providers.health import (
    HealthStatus,
    check_all_providers,
    check_provider_health,
)
from app.services.providers.logging import ProviderLogger
from app.services.providers.metrics import MetricsCollector, get_metrics_collector
from app.services.providers.rate_limiter import RateLimiterRegistry, TokenBucketRateLimiter
from app.services.providers.registry import ProviderNotFoundError, ProviderRegistry
from app.services.providers.request_manager import RequestManager
from app.services.providers.response import AggregateSearchResult, ProviderSearchResult
from app.services.providers.retry import retry_async, with_retry
from app.services.providers.utils import (
    clean_text,
    join_url,
    parse_relative_date,
    parse_salary,
)

# ── RawJobData ──


class TestRawJobData:
    def test_defaults(self):
        job = RawJobData(title="Engineer", company_name="Acme")
        assert job.title == "Engineer"
        assert job.company_name == "Acme"
        assert job.remote is False
        assert job.skills == []
        assert job.raw is None

    def test_all_fields(self):
        job = RawJobData(
            title="Engineer",
            company_name="Acme",
            description="Build things",
            location="Remote",
            url="https://acme.com/job",
            source_job_id="123",
            salary_min=50000.0,
            salary_max=100000.0,
            salary_currency="USD",
            salary_period="yearly",
            remote=True,
            skills=["Python"],
            categories=["Engineering"],
            raw={"source": "test"},
        )
        assert job.title == "Engineer"
        assert job.remote is True
        assert job.skills == ["Python"]
        assert job.raw == {"source": "test"}


# ── ProviderSettings ──


class TestProviderSettings:
    def test_defaults(self):
        s = ProviderSettings(name="test_provider")
        assert s.name == "test_provider"
        assert s.enabled is True
        assert s.requests_per_second == 1.0
        assert s.max_retries == 3

    def test_custom_values(self):
        s = ProviderSettings(
            name="custom", base_url="https://api.example.com", api_key="secret",
            requests_per_second=0.5, max_retries=5, timeout_seconds=60.0,
        )
        assert s.base_url == "https://api.example.com"
        assert s.api_key == "secret"
        assert s.requests_per_second == 0.5

    def test_predefined_configs(self):
        assert "linkedin" in PROVIDER_CONFIGS
        assert "indeed" in PROVIDER_CONFIGS
        assert "greenhouse" in PROVIDER_CONFIGS
        assert "remoteok" in PROVIDER_CONFIGS
        assert PROVIDER_CONFIGS["remoteok"].base_url == "https://remoteok.com"


# ── Error Classes ──


class TestProviderErrors:
    def test_base_error(self):
        e = ProviderError("Something broke", provider="test")
        assert str(e) == "Something broke"
        assert e.provider == "test"

    def test_auth_error(self):
        e = ProviderAuthError("Bad token", provider="test")
        assert "Auth error" in str(e)

    def test_rate_limit_error(self):
        e = ProviderRateLimitError("Too fast", provider="test", retry_after=30.0)
        assert "Rate limited" in str(e)
        assert e.retry_after == 30.0

    def test_timeout_error(self):
        e = ProviderTimeoutError("Timed out", provider="test", timeout=10.0)
        assert "Timeout" in str(e)
        assert e.timeout == 10.0

    def test_parse_error(self):
        e = ProviderParseError("Bad JSON", provider="test", raw="{bad}")
        assert "Parse error" in str(e)
        assert e.raw == "{bad}"

    def test_unavailable_error(self):
        e = ProviderUnavailableError("Down", provider="test")
        assert "Unavailable" in str(e)

    def test_error_hierarchy(self):
        assert issubclass(ProviderAuthError, ProviderError)
        assert issubclass(ProviderRateLimitError, ProviderError)
        assert issubclass(ProviderTimeoutError, ProviderError)
        assert issubclass(ProviderParseError, ProviderError)
        assert issubclass(ProviderUnavailableError, ProviderError)


# ── TokenBucketRateLimiter ──


class TestTokenBucketRateLimiter:
    @pytest.mark.asyncio
    async def test_acquire_returns_zero_when_tokens_available(self):
        limiter = TokenBucketRateLimiter(rate=10.0, burst=5)
        wait = await limiter.acquire()
        assert wait == 0.0

    @pytest.mark.asyncio
    async def test_acquire_waits_when_no_tokens(self):
        limiter = TokenBucketRateLimiter(rate=0.1, burst=1)
        await limiter.acquire()
        wait = await limiter.acquire()
        assert wait > 0

    def test_initial_tokens_equal_burst(self):
        limiter = TokenBucketRateLimiter(rate=5.0, burst=10)
        assert limiter.tokens == 10.0


class TestRateLimiterRegistry:
    def test_get_creates_new_limiter(self):
        registry = RateLimiterRegistry()
        limiter = registry.get("test", rate=2.0)
        assert limiter.rate == 2.0

    def test_get_returns_same_limiter(self):
        registry = RateLimiterRegistry()
        limiter1 = registry.get("test")
        limiter2 = registry.get("test")
        assert limiter1 is limiter2

    def test_remove(self):
        registry = RateLimiterRegistry()
        registry.get("test")
        registry.remove("test")
        # Should create a new one
        limiter = registry.get("test")
        assert limiter is not None


# ── ProviderRegistry ──


DUMMY_SETTINGS = ProviderSettings(
    name="dummy",
    enabled=True,
    base_url="https://example.com",
)

class DummyProvider(BaseProvider):
    def __init__(self, settings: ProviderSettings | None = None) -> None:
        super().__init__(settings or DUMMY_SETTINGS)

    @property
    def name(self) -> str:
        return "dummy"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        return [RawJobData(title=query, company_name="Dummy")]


class DisabledDummyProvider(BaseProvider):
    def __init__(self) -> None:
        settings = ProviderSettings(name="disabled_dummy", enabled=False, base_url="https://example.com")
        super().__init__(settings)

    @property
    def name(self) -> str:
        return "disabled_dummy"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        return []


class TestProviderRegistry:
    def test_register_and_get(self):
        registry = ProviderRegistry()
        provider = DummyProvider()
        registry.register(provider)
        assert registry.get("dummy") is provider

    def test_get_not_found(self):
        registry = ProviderRegistry()
        with pytest.raises(ProviderNotFoundError):
            registry.get("nonexistent")

    def test_get_enabled(self):
        registry = ProviderRegistry()
        p1 = DummyProvider()
        p2 = DisabledDummyProvider()
        registry.register(p1)
        registry.register(p2)
        enabled = registry.get_enabled()
        assert "dummy" in enabled
        assert "disabled_dummy" not in enabled

    def test_len(self):
        registry = ProviderRegistry()
        assert len(registry) == 0
        registry.register(DummyProvider())
        assert len(registry) == 1

    @pytest.mark.asyncio
    async def test_search_all(self):
        registry = ProviderRegistry()
        provider = DummyProvider()
        registry.register(provider)
        results = await registry.search_all("Python Developer")
        assert "dummy" in results
        assert len(results["dummy"]) == 1
        assert results["dummy"][0].title == "Python Developer"


# ── ProviderFactory ──


class TestProviderFactory:
    def test_register_and_create(self):
        factory = ProviderFactory()
        factory.register_class("dummy", DummyProvider)
        provider = factory.create("dummy")
        assert provider.name == "dummy"

    def test_create_unknown(self):
        factory = ProviderFactory()
        with pytest.raises(ValueError):
            factory.create("nonexistent")

    def test_create_all(self):
        factory = ProviderFactory()
        factory.register_class("a", DummyProvider)
        factory.register_class("b", DummyProvider)
        result = factory.create_all(["a", "b"])
        assert len(result) == 2
        assert "a" in result
        assert "b" in result

    def test_create_all_skips_unknown(self):
        factory = ProviderFactory()
        factory.register_class("known", DummyProvider)
        result = factory.create_all(["known", "unknown"])
        assert len(result) == 1

    def test_factory_singleton(self):
        f1 = get_provider_factory()
        f2 = get_provider_factory()
        assert f1 is f2


# ── RequestManager ──


@pytest.mark.asyncio
async def test_request_manager_creates_client():
    settings = ProviderSettings(name="test", base_url="https://example.com")
    rm = RequestManager("test", settings)
    assert rm._client is None or rm._client.is_closed
    await rm.close()


# ── Retry ──


class TestRetryAsync:
    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        fn = AsyncMock(return_value="ok")
        result = await retry_async(fn, max_retries=3, provider="test")
        assert result == "ok"
        assert fn.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        fn = AsyncMock(side_effect=ProviderRateLimitError("too fast", provider="test"))
        with pytest.raises(ProviderUnavailableError):
            await retry_async(fn, max_retries=1, provider="test")
        assert fn.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_non_retryable_error(self):
        fn = AsyncMock(side_effect=ProviderAuthError("bad auth", provider="test"))
        with pytest.raises(ProviderAuthError):
            await retry_async(fn, max_retries=3, provider="test")
        assert fn.call_count == 1


class TestWithRetryDecorator:
    @pytest.mark.asyncio
    async def test_decorator(self):
        call_count = 0

        class TestService:
            @with_retry(max_retries=2)
            async def fetch(self, value: str) -> str:
                nonlocal call_count
                call_count += 1
                return f"result:{value}"

        svc = TestService()
        result = await svc.fetch("hello")
        assert result == "result:hello"
        assert call_count == 1


# ── ProviderLogger ──


class TestProviderLogger:
    def test_creates_logger(self):
        log = ProviderLogger("test_provider")
        assert log.provider_name == "test_provider"

    def test_log_methods_exist(self):
        log = ProviderLogger("test")
        log.info("test event")
        log.warning("test warning")
        log.error("test error")
        log.debug("test debug")


# ── MetricsCollector ──


class TestMetricsCollector:
    def setup_method(self):
        self.metrics = MetricsCollector()

    def test_record_request_success(self):
        self.metrics.record_request("test", success=True, duration_ms=100.0)
        m = self.metrics.get_metrics("test")["test"]
        assert m.total_requests == 1
        assert m.successful_requests == 1
        assert m.failed_requests == 0

    def test_record_request_failure(self):
        self.metrics.record_request("test", success=False, duration_ms=50.0)
        m = self.metrics.get_metrics("test")["test"]
        assert m.total_requests == 1
        assert m.successful_requests == 0
        assert m.failed_requests == 1

    def test_record_rate_limit(self):
        self.metrics.record_rate_limit("test")
        m = self.metrics.get_metrics("test")["test"]
        assert m.rate_limited_count == 1

    def test_record_jobs_found(self):
        self.metrics.record_jobs_found("test", 10)
        m = self.metrics.get_metrics("test")["test"]
        assert m.total_jobs_found == 10

    def test_summary(self):
        self.metrics.record_request("p1", success=True, duration_ms=100.0)
        self.metrics.record_request("p1", success=False, duration_ms=50.0)
        self.metrics.record_jobs_found("p1", 5)
        summary = self.metrics.summary()
        assert "p1" in summary
        assert summary["p1"]["total_requests"] == 2

    def test_reset(self):
        self.metrics.record_request("test", success=True, duration_ms=10.0)
        self.metrics.reset("test")
        m = self.metrics.get_metrics("test")["test"]
        assert m.total_requests == 0


class TestMetricsCollectorSingleton:
    def test_singleton(self):
        c1 = get_metrics_collector()
        c2 = get_metrics_collector()
        assert c1 is c2


# ── Health Checks ──


class TestHealthStatus:
    def test_to_dict(self):
        status = HealthStatus(name="test", available=True, latency_ms=50.0)
        d = status.to_dict()
        assert d["name"] == "test"
        assert d["available"] is True
        assert d["latency_ms"] == 50.0


@pytest.mark.asyncio
async def test_check_provider_health_without_base_url():
    provider = DummyProvider()
    provider.settings.base_url = ""
    status = await check_provider_health(provider)
    assert status.available is True
    assert status.name == "dummy"


@pytest.mark.asyncio
async def test_check_all_providers():
    registry = ProviderRegistry()
    registry.register(DummyProvider())
    results = await check_all_providers(registry)
    assert len(results) >= 1
    assert all(isinstance(r, HealthStatus) for r in results)


# ── Response Objects ──


class TestProviderSearchResult:
    def test_defaults(self):
        r = ProviderSearchResult(provider="test")
        assert r.provider == "test"
        assert r.jobs == []
        assert r.success is True

    def test_with_jobs(self):
        job = RawJobData(title="Engineer", company_name="Acme")
        r = ProviderSearchResult(provider="test", jobs=[job], query="engineer")
        assert len(r.jobs) == 1
        assert r.query == "engineer"


class TestAggregateSearchResult:
    def test_empty(self):
        agg = AggregateSearchResult()
        assert agg.all_jobs() == []
        assert agg.total_jobs == 0

    def test_with_results(self):
        r1 = ProviderSearchResult(
            provider="p1",
            jobs=[RawJobData(title="Job1", company_name="C1")],
        )
        r2 = ProviderSearchResult(
            provider="p2",
            jobs=[RawJobData(title="Job2", company_name="C2")],
        )
        agg = AggregateSearchResult(results=[r1, r2])
        assert agg.total_jobs == 0
        assert len(agg.all_jobs()) == 2
        assert agg.successful_providers() == ["p1", "p2"]

    def test_providers_with_errors(self):
        r1 = ProviderSearchResult(provider="p1", success=False, error="Failed")
        r2 = ProviderSearchResult(provider="p2", success=True)
        agg = AggregateSearchResult(results=[r1, r2])
        assert agg.providers_with_errors() == ["p1"]
        assert agg.successful_providers() == ["p2"]


# ── Shared Utilities ──


class TestParseSalary:
    def test_none(self):
        assert parse_salary(None) == {"min": None, "max": None, "currency": None, "period": None}

    def test_empty(self):
        assert parse_salary("") == {"min": None, "max": None, "currency": None, "period": None}

    def test_range(self):
        result = parse_salary("$50,000 - $70,000 a year")
        assert result["min"] == 50000.0
        assert result["max"] == 70000.0
        assert result["currency"] == "USD"
        assert result["period"] == "yearly"

    def test_single_value(self):
        result = parse_salary("$100,000 annual")
        assert result["min"] == 100000.0
        assert result["currency"] == "USD"
        assert result["period"] == "yearly"

    def test_hourly(self):
        result = parse_salary("$25 - $35 per hour")
        assert result["min"] == 25.0
        assert result["max"] == 35.0
        assert result["period"] == "hourly"

    def test_euro(self):
        result = parse_salary("€40,000 - €60,000")
        assert result["currency"] == "EUR"

    def test_gbp(self):
        result = parse_salary("£30,000")
        assert result["currency"] == "GBP"

    def test_k_format(self):
        result = parse_salary("$80k - $120k")
        assert result["min"] == 80000.0
        assert result["max"] == 120000.0


class TestParseRelativeDate:
    def test_none(self):
        assert parse_relative_date(None) is None

    def test_empty(self):
        assert parse_relative_date("") is None

    def test_just_posted(self):
        result = parse_relative_date("Just posted")
        assert result is not None

    def test_today(self):
        result = parse_relative_date("Today")
        assert result is not None

    def test_days_ago(self):
        result = parse_relative_date("5 days ago")
        assert result is not None

    def test_hours_ago(self):
        result = parse_relative_date("3 hours ago")
        assert result is not None

    def test_weeks_ago(self):
        result = parse_relative_date("2 weeks ago")
        assert result is not None


class TestCleanText:
    def test_none(self):
        assert clean_text(None) is None

    def test_empty(self):
        assert clean_text("") is None

    def test_whitespace_collapse(self):
        assert clean_text("  Hello   World  ") == "Hello World"

    def test_truncate(self):
        text = "a" * 300
        result = clean_text(text, max_length=100)
        assert len(result) == 100

    def test_no_truncate(self):
        result = clean_text("Hello", max_length=100)
        assert result == "Hello"


class TestJoinURL:
    def test_basic(self):
        assert join_url("https://example.com", "path") == "https://example.com/path"

    def test_with_slashes(self):
        assert join_url("https://example.com/", "/path/") == "https://example.com/path/"

    def test_no_base_slash(self):
        assert join_url("https://example.com/api", "v1/jobs") == "https://example.com/api/v1/jobs"


# ── ProviderConfigs ──


class TestProviderConfigs:
    def test_all_providers_have_configs(self):
        expected = [
            "linkedin", "indeed", "wellfound", "greenhouse", "lever",
            "ashby", "workday", "google_jobs", "remoteok", "weworkremotely",
            "career_pages", "ycombinator", "naukri", "foundit",
            "internshala", "unstop", "freshersworld",
        ]
        for name in expected:
            assert name in PROVIDER_CONFIGS, f"Missing config for {name}"

    def test_all_configs_have_base_url_or_explicit_empty(self):
        for name, config in PROVIDER_CONFIGS.items():
            if name in ("workday", "career_pages"):
                assert config.base_url == ""
            else:
                assert config.base_url != "", f"Empty base_url for {name}"
