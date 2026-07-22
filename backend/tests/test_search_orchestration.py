from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.jobs.config import (
    JobDiscoveryConfig,
)
from app.jobs.orchestration.health_manager import ProviderHealthManager
from app.jobs.orchestration.provider_selector import ProviderSelector
from app.jobs.orchestration.search_aggregator import SearchAggregator
from app.jobs.orchestration.search_cache import SearchCache
from app.jobs.orchestration.search_metrics import SearchMetrics
from app.jobs.orchestration.search_orchestrator import SearchOrchestrator
from app.jobs.orchestration.search_ranking import RankingFactors, SearchRanking
from app.jobs.registry import JobProviderRegistry
from app.jobs.schemas import (
    CompanyInfo,
    EmploymentType,
    ExperienceLevel,
    JobPosting,
    JobSearchRequest,
    LocationInfo,
    RemoteType,
    SalaryInfo,
)


def make_config(**overrides) -> JobDiscoveryConfig:
    return JobDiscoveryConfig(**overrides)


def make_posting(
    title: str = "Engineer",
    provider: str = "mock",
    provider_job_id: str = "1",
    url: str = "https://example.com/job/1",
    posted_date: datetime | None = None,
    remote_type: RemoteType = RemoteType.ON_SITE,
    salary: SalaryInfo | None = None,
    company_name: str = "Acme",
    skills: list[str] | None = None,
    description: str = "",
    employment_type: EmploymentType = EmploymentType.FULL_TIME,
    experience_level: ExperienceLevel = ExperienceLevel.MID,
) -> JobPosting:
    return JobPosting(
        title=title,
        provider=provider,
        provider_job_id=provider_job_id,
        url=url,
        posted_date=posted_date or datetime(2025, 1, 1, tzinfo=timezone.utc),
        company=CompanyInfo(name=company_name),
        location=LocationInfo(remote_type=remote_type, display_name="Somewhere"),
        salary=salary,
        skills=skills or [],
        description=description,
        employment_type=employment_type,
        experience_level=experience_level,
    )


class TestSearchCache:
    def test_cache_hit_and_miss(self):
        cache = SearchCache(ttl_seconds=300)
        req = JobSearchRequest(query="python")
        assert cache.get(req) is None
        resp = cache.get(req)
        assert resp is None
        stats = cache.stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0

    def test_set_and_get(self):
        cache = SearchCache(ttl_seconds=300)
        req = JobSearchRequest(query="python")
        from app.jobs.schemas import JobSearchResponse, SearchMetadata

        resp = JobSearchResponse(
            results=[make_posting()],
            metadata=SearchMetadata(total_results=1),
        )
        cache.set(req, resp)
        cached = cache.get(req)
        assert cached is not None
        assert len(cached.results) == 1
        assert cache.stats()["hits"] == 1

    def test_cache_ttl_expiry(self):
        cache = SearchCache(ttl_seconds=0)
        req = JobSearchRequest(query="python")
        from app.jobs.schemas import JobSearchResponse, SearchMetadata

        resp = JobSearchResponse(
            results=[make_posting()],
            metadata=SearchMetadata(total_results=1),
        )
        cache.set(req, resp)
        assert cache.get(req) is None

    def test_cache_does_not_store_empty(self):
        cache = SearchCache(ttl_seconds=300)
        req = JobSearchRequest(query="nothing")
        from app.jobs.schemas import JobSearchResponse, SearchMetadata

        resp = JobSearchResponse(
            results=[],
            metadata=SearchMetadata(total_results=0),
        )
        cache.set(req, resp)
        assert cache.get(req) is None

    def test_cache_key_differentiates_requests(self):
        cache = SearchCache(ttl_seconds=300)
        req1 = JobSearchRequest(query="python")
        req2 = JobSearchRequest(query="java")
        from app.jobs.schemas import JobSearchResponse, SearchMetadata

        resp1 = JobSearchResponse(
            results=[make_posting(title="Python Dev")],
            metadata=SearchMetadata(total_results=1),
        )
        cache.set(req1, resp1)
        assert cache.get(req2) is None

    def test_invalidate_all(self):
        cache = SearchCache(ttl_seconds=300)
        from app.jobs.schemas import JobSearchResponse, SearchMetadata

        for q in ["python", "java", "go"]:
            req = JobSearchRequest(query=q)
            resp = JobSearchResponse(
                results=[make_posting(title=q)],
                metadata=SearchMetadata(total_results=1),
            )
            cache.set(req, resp)
        assert cache.stats()["size"] == 3
        removed = cache.invalidate()
        assert removed == 3
        assert cache.stats()["size"] == 0

    def test_max_size_eviction(self):
        cache = SearchCache(ttl_seconds=300, max_size=2)
        from app.jobs.schemas import JobSearchResponse, SearchMetadata

        for q in ["a", "b", "c"]:
            req = JobSearchRequest(query=q)
            resp = JobSearchResponse(
                results=[make_posting(title=q)],
                metadata=SearchMetadata(total_results=1),
            )
            cache.set(req, resp)
        assert cache.stats()["size"] <= 2

    def test_clear_resets_stats(self):
        cache = SearchCache(ttl_seconds=300)
        cache.get(JobSearchRequest(query="x"))
        cache.clear()
        s = cache.stats()
        assert s["hits"] == 0
        assert s["misses"] == 0
        assert s["size"] == 0

    def test_hit_ratio(self):
        cache = SearchCache(ttl_seconds=300)
        assert cache.stats()["hit_ratio"] == 0.0
        from app.jobs.schemas import JobSearchResponse, SearchMetadata

        req = JobSearchRequest(query="python")
        cache.set(
            req,
            JobSearchResponse(
                results=[make_posting()],
                metadata=SearchMetadata(total_results=1),
            ),
        )
        cache.get(req)
        cache.get(req)
        cache.get(JobSearchRequest(query="other"))
        ratio = cache.stats()["hit_ratio"]
        assert 0.5 < ratio <= 1.0


class TestProviderHealthManager:
    def test_initial_state_is_healthy(self):
        mgr = ProviderHealthManager(min_samples=1)
        assert mgr.is_healthy("provider_a") is True

    def test_healthy_after_successes(self):
        mgr = ProviderHealthManager(min_samples=1)
        mgr.record_success("p1")
        mgr.record_success("p1")
        assert mgr.is_healthy("p1") is True

    def test_failure_deprioritization(self):
        mgr = ProviderHealthManager(
            min_samples=1,
            failure_threshold=0.5,
            cooldown_seconds=10,
        )
        mgr.record_failure("p1")
        mgr.record_failure("p1")
        assert mgr.is_deprioritized("p1") is True
        assert mgr.is_healthy("p1") is False

    def test_healthy_after_recovery(self):
        mgr = ProviderHealthManager(
            min_samples=1,
            failure_threshold=0.5,
            cooldown_seconds=0,
        )
        mgr.record_failure("p1")
        mgr.record_success("p1")
        mgr.record_success("p1")
        assert mgr.is_healthy("p1") is True
        assert mgr.is_deprioritized("p1") is False

    def test_latency_threshold(self):
        mgr = ProviderHealthManager(
            min_samples=1,
            latency_threshold_ms=50.0,
        )
        mgr.record_success("p1", latency_ms=100.0)
        assert mgr.is_healthy("p1") is False

    def test_failure_rate(self):
        mgr = ProviderHealthManager(min_samples=1)
        mgr.record_success("p1")
        mgr.record_failure("p1")
        rate = mgr.get_failure_rate("p1")
        assert rate == 0.5

    def test_failure_rate_insufficient_samples(self):
        mgr = ProviderHealthManager(min_samples=10)
        mgr.record_success("p1")
        assert mgr.get_failure_rate("p1") is None

    def test_summary(self):
        mgr = ProviderHealthManager(min_samples=1)
        mgr.record_success("p1", latency_ms=10.0)
        mgr.record_failure("p2")
        summary = mgr.summary()
        assert "p1" in summary
        assert "p2" in summary
        assert summary["p1"]["healthy"] is True
        assert summary["p1"]["failures"] == 0

    def test_avg_latency(self):
        mgr = ProviderHealthManager(min_samples=1)
        mgr.record_success("p1", latency_ms=100.0)
        mgr.record_success("p1", latency_ms=200.0)
        avg = mgr.get_avg_latency("p1")
        assert avg == 150.0

    def test_avg_latency_no_records(self):
        mgr = ProviderHealthManager()
        assert mgr.get_avg_latency("nonexistent") is None


class TestSearchMetrics:
    def test_record_search(self):
        metrics = SearchMetrics()
        metrics.record_search(
            duration_ms=100.0,
            provider_latencies={"p1": 50.0},
            cache_hit=False,
            jobs_before_dedup=20,
            jobs_after_dedup=15,
            provider_failures=["p2"],
            providers_queried=["p1", "p2"],
        )
        summary = metrics.summary()
        assert summary["total_searches"] == 1
        assert summary["avg_duration_ms"] == 100.0
        assert summary["total_jobs_before_dedup"] == 20
        assert summary["total_jobs_after_dedup"] == 15
        assert summary["total_duplicates_removed"] == 5
        assert "p1" in summary["provider_stats"]
        assert summary["provider_stats"]["p2"]["failures"] == 1

    def test_cache_hit_tracking(self):
        metrics = SearchMetrics()
        metrics.record_search(
            duration_ms=0,
            provider_latencies={},
            cache_hit=True,
            jobs_before_dedup=0,
            jobs_after_dedup=0,
            provider_failures=[],
            providers_queried=["mock"],
        )
        metrics.record_search(
            duration_ms=200.0,
            provider_latencies={"p1": 100.0},
            cache_hit=False,
            jobs_before_dedup=10,
            jobs_after_dedup=8,
            provider_failures=[],
            providers_queried=["p1"],
        )
        s = metrics.summary()
        assert s["cache_hits"] == 1
        assert s["cache_misses"] == 1
        assert s["cache_hit_ratio"] == 0.5

    def test_multiple_searches(self):
        metrics = SearchMetrics()
        metrics.record_search(
            duration_ms=100.0,
            provider_latencies={"p1": 50.0},
            cache_hit=False,
            jobs_before_dedup=10,
            jobs_after_dedup=9,
            provider_failures=["p2"],
            providers_queried=["p1", "p2"],
        )
        metrics.record_search(
            duration_ms=200.0,
            provider_latencies={"p1": 75.0},
            cache_hit=False,
            jobs_before_dedup=20,
            jobs_after_dedup=18,
            provider_failures=[],
            providers_queried=["p1"],
        )
        s = metrics.summary()
        assert s["total_searches"] == 2
        assert s["avg_duration_ms"] == 150.0
        assert s["total_jobs_before_dedup"] == 30
        assert s["total_jobs_after_dedup"] == 27
        assert s["provider_stats"]["p1"]["avg_latency_ms"] == 62.5
        assert s["provider_stats"]["p2"]["failures"] == 1

    def test_reset(self):
        metrics = SearchMetrics()
        metrics.record_search(
            duration_ms=100.0,
            provider_latencies={},
            cache_hit=False,
            jobs_before_dedup=10,
            jobs_after_dedup=8,
            provider_failures=[],
            providers_queried=["p1"],
        )
        metrics.reset()
        s = metrics.summary()
        assert s["total_searches"] == 0

    def test_empty_summary(self):
        metrics = SearchMetrics()
        s = metrics.summary()
        assert s["total_searches"] == 0
        assert s["avg_duration_ms"] == 0.0
        assert s["cache_hit_ratio"] == 0.0


class TestSearchRanking:
    def test_rank_freshness_newer_first(self):
        ranker = SearchRanking()
        now = datetime.now(timezone.utc)
        old = make_posting(title="Old", posted_date=datetime(2024, 1, 1, tzinfo=timezone.utc))
        new = make_posting(title="New", posted_date=now)
        request = JobSearchRequest(query="engineer")
        ranked = ranker.rank([old, new], request)
        assert ranked[0].title == "New"
        assert ranked[1].title == "Old"

    def test_rank_salary_has_boost(self):
        ranker = SearchRanking()
        has_salary = make_posting(title="Paid", salary=SalaryInfo(min_amount=100000))
        no_salary = make_posting(title="Unpaid", salary=None)
        request = JobSearchRequest(query="engineer")
        ranked = ranker.rank([no_salary, has_salary], request)
        assert ranked[0].title == "Paid"

    def test_rank_remote_preference(self):
        ranker = SearchRanking()
        remote = make_posting(title="Remote Job", remote_type=RemoteType.REMOTE)
        onsite = make_posting(title="Onsite Job", remote_type=RemoteType.ON_SITE)
        request = JobSearchRequest(query="engineer")
        ranked = ranker.rank([onsite, remote], request)
        assert ranked[0].title == "Remote Job"

    def test_rank_keyword_relevance(self):
        ranker = SearchRanking()
        relevant = make_posting(title="Python Developer", skills=["python"], description="Python backend")
        irrelevant = make_posting(title="Frontend Developer", skills=["javascript"])
        request = JobSearchRequest(query="python")
        ranked = ranker.rank([irrelevant, relevant], request)
        assert ranked[0].title == "Python Developer"

    def test_rank_keywords_list(self):
        ranker = SearchRanking()
        relevant = make_posting(title="Data Engineer", skills=["python", "spark"], description="python spark")
        irrelevant = make_posting(title="Designer")
        request = JobSearchRequest(keywords=["python", "spark"])
        ranked = ranker.rank([irrelevant, relevant], request)
        assert ranked[0].title == "Data Engineer"

    def test_rank_provider_quality(self):
        factors = RankingFactors(provider_quality={"premium": 2.0, "basic": 0.5})
        ranker = SearchRanking(factors)
        premium = make_posting(title="Premium Job", provider="premium")
        basic = make_posting(title="Basic Job", provider="basic")
        request = JobSearchRequest(query="job")
        ranked = ranker.rank([basic, premium], request)
        assert ranked[0].provider == "premium"

    def test_rank_custom_factors(self):
        ranker = SearchRanking()
        custom = RankingFactors(
            freshness_weight=1.0,
            salary_weight=0.0,
            remote_weight=0.0,
            keyword_weight=0.0,
            provider_weight=0.0,
        )
        now = datetime.now(timezone.utc)
        old = make_posting(title="Old", posted_date=datetime(2024, 1, 1, tzinfo=timezone.utc))
        new = make_posting(title="New", posted_date=now)
        request = JobSearchRequest(query="engineer")
        ranked = ranker.rank([old, new], request, factors=custom)
        assert ranked[0].title == "New"

    def test_factors_merge(self):
        f = RankingFactors()
        merged = f.merge({"freshness_weight": 0.5})
        assert merged.freshness_weight == 0.5
        assert merged.salary_weight == 0.20
        assert merged.remote_weight == 0.15

    def test_factors_to_dict(self):
        f = RankingFactors()
        d = f.to_dict()
        assert "freshness_weight" in d
        assert "provider_weight" in d

    def test_rank_empty(self):
        ranker = SearchRanking()
        result = ranker.rank([], JobSearchRequest(query="test"))
        assert result == []

    def test_no_date_default_score(self):
        ranker = SearchRanking()
        no_date = make_posting(title="No Date", posted_date=None)
        has_date = make_posting(title="Has Date")
        request = JobSearchRequest(query="job")
        ranked = ranker.rank([no_date, has_date], request)
        assert len(ranked) == 2


class TestProviderSelector:
    def test_select_enabled_providers(self):
        config = make_config(enabled_providers=["mock"])
        registry = JobProviderRegistry()
        selector = ProviderSelector(registry, config)
        with patch.object(registry, "list_providers", return_value=["mock", "other"]):
            selected = selector.select(JobSearchRequest(query="test"))
            assert "mock" in selected
            assert "other" not in selected

    def test_select_requested_providers(self):
        config = make_config(enabled_providers=["mock"])
        registry = JobProviderRegistry()
        selector = ProviderSelector(registry, config)
        with patch.object(registry, "is_registered", return_value=True):
            selected = selector.select(JobSearchRequest(query="test", providers=["other"]))
            assert selected == ["other"]

    def test_select_skips_unhealthy(self):
        config = make_config(enabled_providers=["p1", "p2"])
        registry = JobProviderRegistry()
        health = ProviderHealthManager(min_samples=1, failure_threshold=0.1)
        health.record_failure("p2")
        health.record_failure("p2")
        selector = ProviderSelector(registry, config, health)
        with patch.object(registry, "list_providers", return_value=["p1", "p2"]):
            selected = selector.select(JobSearchRequest(query="test"))
            assert "p1" in selected
            assert "p2" not in selected

    def test_startup_provider_classification(self):
        assert ProviderSelector.is_startup_provider("wellfound") is True
        assert ProviderSelector.is_startup_provider("y_combinator") is True
        assert ProviderSelector.is_startup_provider("mock") is False

    def test_ats_provider_classification(self):
        assert ProviderSelector.is_ats_provider("greenhouse") is True
        assert ProviderSelector.is_ats_provider("lever") is True
        assert ProviderSelector.is_ats_provider("mock") is False

    def test_select_prefers_healthy_over_deprioritized(self):
        config = make_config(enabled_providers=["p1", "p2"])
        registry = JobProviderRegistry()
        health = ProviderHealthManager(min_samples=1, failure_threshold=0.1, cooldown_seconds=60)
        health.record_failure("p2")
        health.record_failure("p2")
        selector = ProviderSelector(registry, config, health)
        with (
            patch.object(registry, "list_providers", return_value=["p1", "p2"]),
            patch.object(health, "is_healthy", return_value=True),
            patch.object(health, "is_deprioritized", side_effect=lambda p: p == "p2"),
        ):
            selected = selector.select(JobSearchRequest(query="test"))
        assert selected.index("p1") < selected.index("p2")


class TestSearchAggregator:
    def test_aggregate_single_provider(self):
        config = make_config()
        agg = SearchAggregator(config)
        results = {
            "mock": [make_posting(provider="mock", title="Job1")],
        }
        response = agg.aggregate(results, JobSearchRequest())
        assert len(response.results) == 1
        assert response.results[0].title == "Job1"

    def test_aggregate_multiple_providers(self):
        config = make_config()
        agg = SearchAggregator(config)
        results = {
            "p1": [make_posting(provider="p1", title="Job1")],
            "p2": [make_posting(provider="p2", title="Job2")],
        }
        response = agg.aggregate(results, JobSearchRequest())
        assert len(response.results) == 2

    def test_aggregate_deduplication(self):
        config = make_config(dedup_by_url=True, dedup_by_provider_id=False)
        agg = SearchAggregator(config)
        results = {
            "p1": [
                make_posting(provider="p1", url="https://example.com/job/1", provider_job_id="1"),
            ],
            "p2": [
                make_posting(provider="p2", url="https://example.com/job/1", provider_job_id="2"),
            ],
        }
        response = agg.aggregate(results, JobSearchRequest())
        assert len(response.results) == 1
        assert response.metadata.duplicates_removed == 1

    def test_aggregate_deduplication_disabled(self):
        config = make_config(dedup_by_url=True, dedup_by_provider_id=False)
        agg = SearchAggregator(config)
        results = {
            "p1": [make_posting(provider="p1", url="https://ex.com/job/1")],
            "p2": [make_posting(provider="p2", url="https://ex.com/job/1")],
        }
        response = agg.aggregate(results, JobSearchRequest(deduplicate=False))
        assert len(response.results) == 2

    def test_aggregate_pagination(self):
        config = make_config()
        agg = SearchAggregator(config)
        postings = [
            make_posting(provider="p1", title=f"Job{i}", provider_job_id=str(i), url=f"https://ex.com/job/{i}")
            for i in range(10)
        ]
        results = {"p1": postings}
        response = agg.aggregate(results, JobSearchRequest(limit=3))
        assert len(response.results) == 3
        assert response.metadata.total_results == 10

    def test_aggregate_metadata(self):
        config = make_config()
        agg = SearchAggregator(config)
        results = {
            "p1": [make_posting(provider="p1")],
            "p2": None,
        }
        response = agg.aggregate(results, JobSearchRequest())
        assert "p1" in response.metadata.providers_queried
        assert "p1" in response.metadata.providers_succeeded
        assert response.metadata.providers_failed[0]["provider"] == "p2"
        assert response.metadata.duration_ms is None

    def test_aggregate_filtering(self):
        config = make_config()
        agg = SearchAggregator(config)
        results = {
            "p1": [
                make_posting(title="Java Dev", provider_job_id="j1", url="https://ex.com/job/j1", description="java"),
                make_posting(
                    title="Python Dev", provider_job_id="p1", url="https://ex.com/job/p1", description="python"
                ),
            ],
        }
        response = agg.aggregate(results, JobSearchRequest(query="python"))
        assert len(response.results) >= 1

    def test_aggregate_empty(self):
        config = make_config()
        agg = SearchAggregator(config)
        response = agg.aggregate({}, JobSearchRequest())
        assert len(response.results) == 0
        assert response.metadata.total_results == 0


class TestSearchOrchestrator:
    @pytest.fixture
    def config(self):
        return make_config(
            enabled_providers=["mock"],
            max_concurrency=5,
            provider_timeout_seconds=10,
            cache_ttl_seconds=300,
            metrics_enabled=True,
        )

    @pytest.fixture
    def registry(self):
        reg = JobProviderRegistry()
        from app.jobs.providers.mock import MockJobProvider

        reg.register(MockJobProvider(make_config()))
        return reg

    @pytest.fixture
    def orchestrator(self, config, registry):
        return SearchOrchestrator(registry=registry, config=config)

    async def test_search_returns_results(self, orchestrator):
        response = await orchestrator.search(JobSearchRequest(query="engineer"))
        assert len(response.results) > 0
        assert response.metadata.total_results > 0

    async def test_search_caches_results(self, orchestrator):
        request = JobSearchRequest(query="engineer")
        await orchestrator.search(request)
        stats_before = orchestrator.get_cache_stats()
        hits_before = stats_before["hits"]
        await orchestrator.search(request)
        stats_after = orchestrator.get_cache_stats()
        assert stats_after["hits"] > hits_before

    async def test_search_metrics_collected(self, orchestrator):
        await orchestrator.search(JobSearchRequest(query="engineer"))
        metrics = orchestrator.get_metrics_summary()
        assert metrics["total_searches"] >= 1

    async def test_search_health_tracked(self, orchestrator):
        await orchestrator.search(JobSearchRequest(query="engineer"))
        health = orchestrator.get_health_summary()
        assert "mock" in health
        assert health["mock"]["healthy"] is True

    async def test_cache_invalidate(self, orchestrator):
        await orchestrator.search(JobSearchRequest(query="python"))
        await orchestrator.search(JobSearchRequest(query="java"))
        stats_before = orchestrator.get_cache_stats()
        assert stats_before["size"] >= 1
        removed = orchestrator.invalidate_cache()
        assert removed >= 1
        assert orchestrator.get_cache_stats()["size"] == 0

    async def test_cache_invalidate_by_provider(self, orchestrator):
        await orchestrator.search(JobSearchRequest(query="python"))
        removed = orchestrator.invalidate_cache("mock")
        assert removed >= 1

    async def test_partial_failure(self):
        config = make_config(
            enabled_providers=["good", "bad"],
            max_concurrency=5,
            provider_timeout_seconds=5,
        )
        registry = JobProviderRegistry()

        class GoodProvider:
            name = "good"
            display_name = "Good"
            supports_pagination = False
            supports_filters = False

            def __init__(self, config):
                self.config = config

            async def search_jobs(self, request):
                from app.jobs.schemas import JobSearchResponse, SearchMetadata

                return JobSearchResponse(
                    results=[make_posting(provider="good", title="Good Job", description="good job posting")],
                    metadata=SearchMetadata(providers_queried=["good"], providers_succeeded=["good"]),
                )

            async def health_check(self):
                return True

            async def provider_info(self):
                from app.jobs.schemas import JobProviderInfo

                return JobProviderInfo(name="good", display_name="Good")

        class BadProvider:
            name = "bad"
            display_name = "Bad"
            supports_pagination = False
            supports_filters = False

            def __init__(self, config):
                self.config = config

            async def search_jobs(self, request):
                raise RuntimeError("Provider down")

            async def health_check(self):
                return False

            async def provider_info(self):
                from app.jobs.schemas import JobProviderInfo

                return JobProviderInfo(name="bad", display_name="Bad")

        registry.register(GoodProvider(config))
        registry.register(BadProvider(config))

        orch = SearchOrchestrator(registry=registry, config=config)
        response = await orch.search(JobSearchRequest())
        assert len(response.results) == 1
        assert response.results[0].provider == "good"
        assert len(response.metadata.providers_queried) == 2

    async def test_timeout_handling(self):
        config = make_config(
            enabled_providers=["slow", "fast"],
            max_concurrency=5,
            provider_timeout_seconds=1,
        )
        registry = JobProviderRegistry()

        class SlowProvider:
            name = "slow"
            display_name = "Slow"
            supports_pagination = False
            supports_filters = False

            def __init__(self, config):
                self.config = config

            async def search_jobs(self, request):
                import asyncio

                await asyncio.sleep(10)
                from app.jobs.schemas import JobSearchResponse, SearchMetadata

                return JobSearchResponse(
                    results=[make_posting(provider="slow")],
                    metadata=SearchMetadata(),
                )

            async def health_check(self):
                return True

            async def provider_info(self):
                from app.jobs.schemas import JobProviderInfo

                return JobProviderInfo(name="slow", display_name="Slow")

        class FastProvider:
            name = "fast"
            display_name = "Fast"
            supports_pagination = False
            supports_filters = False

            def __init__(self, config):
                self.config = config

            async def search_jobs(self, request):
                from app.jobs.schemas import JobSearchResponse, SearchMetadata

                return JobSearchResponse(
                    results=[make_posting(provider="fast", title="Fast Job", description="fast job posting")],
                    metadata=SearchMetadata(),
                )

            async def health_check(self):
                return True

            async def provider_info(self):
                from app.jobs.schemas import JobProviderInfo

                return JobProviderInfo(name="fast", display_name="Fast")

        registry.register(SlowProvider(config))
        registry.register(FastProvider(config))

        orch = SearchOrchestrator(registry=registry, config=config)
        response = await orch.search(JobSearchRequest())
        assert len(response.results) >= 1
        assert response.results[0].provider == "fast"

    async def test_ranking_applied(self):
        config = make_config(enabled_providers=["mock"])
        registry = JobProviderRegistry()
        mock_provider = type(
            "RankedMock",
            (),
            {
                "name": "mock",
                "display_name": "Mock",
                "supports_pagination": False,
                "supports_filters": False,
                "config": config,
            },
        )
        mock_provider.search_jobs = AsyncMock(
            return_value=type(
                "R",
                (),
                {
                    "results": [
                        make_posting(title="Job A", posted_date=datetime(2025, 6, 1, tzinfo=timezone.utc)),
                        make_posting(title="Job B", posted_date=datetime(2024, 1, 1, tzinfo=timezone.utc)),
                    ],
                },
            )()
        )
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.provider_info = AsyncMock(return_value=type("I", (), {"name": "mock", "display_name": "Mock"})())
        registry.register(mock_provider)
        orch = SearchOrchestrator(registry=registry, config=config)
        response = await orch.search(JobSearchRequest())
        assert response.results[0].title == "Job A"


class TestPostedWithinFilter:
    def test_naive_datetime(self):
        from app.jobs.filters import PostedWithinFilter

        now = datetime.utcnow()
        recent = make_posting(title="Recent", posted_date=now)
        old = make_posting(title="Old", posted_date=datetime(2020, 1, 1))
        filt = PostedWithinFilter(days=7)
        result = filt.apply([recent, old])
        titles = [p.title for p in result]
        assert "Recent" in titles
        assert "Old" not in titles

    def test_aware_datetime(self):
        from app.jobs.filters import PostedWithinFilter

        now = datetime.now(timezone.utc)
        recent = make_posting(title="Recent", posted_date=now)
        old = make_posting(title="Old", posted_date=datetime(2020, 1, 1, tzinfo=timezone.utc))
        filt = PostedWithinFilter(days=7)
        result = filt.apply([recent, old])
        titles = [p.title for p in result]
        assert "Recent" in titles
        assert "Old" not in titles

    def test_mixed_aware_naive(self):
        from app.jobs.filters import PostedWithinFilter

        aware = make_posting(title="Aware", posted_date=datetime.now(timezone.utc))
        naive = make_posting(title="Naive", posted_date=datetime.utcnow())
        filt = PostedWithinFilter(days=7)
        result = filt.apply([aware, naive])
        assert len(result) == 2

    def test_none_date(self):
        from app.jobs.filters import PostedWithinFilter

        none_posting = JobPosting(
            title="None",
            provider="mock",
            company=CompanyInfo(name="Acme"),
            posted_date=None,
        )
        filt = PostedWithinFilter(days=7)
        result = filt.apply([none_posting])
        assert len(result) == 1

    def test_old_posting_excluded(self):
        from app.jobs.filters import PostedWithinFilter

        old = make_posting(title="Old", posted_date=datetime(2020, 1, 1, tzinfo=timezone.utc))
        filt = PostedWithinFilter(days=1)
        result = filt.apply([old])
        assert len(result) == 0


class TestProviderSelectorWithHealth:
    def test_health_integration(self):
        config = make_config(enabled_providers=["healthy_provider", "sick_provider"])
        registry = JobProviderRegistry()
        health = ProviderHealthManager(min_samples=1, failure_threshold=0.1, cooldown_seconds=60)
        health.record_failure("sick_provider")
        selector = ProviderSelector(registry, config, health)

        hp_cfg = config
        sp_cfg = config

        class HealthyProvider:
            name = "healthy_provider"
            display_name = "Healthy"
            description = ""
            version = "1.0.0"
            supports_pagination = False
            supports_filters = False
            config = hp_cfg

        class SickProvider:
            name = "sick_provider"
            display_name = "Sick"
            description = ""
            version = "1.0.0"
            supports_pagination = False
            supports_filters = False
            config = sp_cfg

        hp = HealthyProvider()
        sp = SickProvider()
        registry.register(hp)
        registry.register(sp)
        selected = selector.select(JobSearchRequest(query="test"))
        assert "sick_provider" not in selected


class TestJobDiscoveryServiceWithOrchestrator:
    async def test_service_with_orchestrator(self):
        config = make_config(enabled_providers=["mock"])
        registry = JobProviderRegistry()
        from app.jobs.providers.mock import MockJobProvider

        registry.register(MockJobProvider(config))
        orch = SearchOrchestrator(registry=registry, config=config)
        from app.jobs.service import JobDiscoveryService

        service = JobDiscoveryService(registry=registry, config=config, orchestrator=orch)
        response = await service.search(JobSearchRequest(query="engineer"))
        assert len(response.results) > 0
        assert response.metadata.duration_ms is not None

    async def test_service_fallback_without_orchestrator(self):
        config = make_config(enabled_providers=["mock"])
        registry = JobProviderRegistry()
        from app.jobs.providers.mock import MockJobProvider

        registry.register(MockJobProvider(config))
        from app.jobs.service import JobDiscoveryService

        service = JobDiscoveryService(registry=registry, config=config)
        response = await service.search(JobSearchRequest(query="engineer"))
        assert len(response.results) > 0

    async def test_service_validation_still_works(self):
        config = make_config(enabled_providers=["mock"])
        registry = JobProviderRegistry()
        from app.jobs.providers.mock import MockJobProvider

        registry.register(MockJobProvider(config))
        orch = SearchOrchestrator(registry=registry, config=config)
        from app.jobs.exceptions import SearchValidationError
        from app.jobs.service import JobDiscoveryService

        service = JobDiscoveryService(registry=registry, config=config, orchestrator=orch)
        with pytest.raises(SearchValidationError):
            await service.search(JobSearchRequest())
