from __future__ import annotations

import pytest

from app.jobs.config import JobDiscoveryConfig
from app.jobs.deduplication import DeduplicationEngine
from app.jobs.exceptions import (
    NormalizationError,
    ProviderNotFoundError,
    SearchValidationError,
)
from app.jobs.filters import (
    EmploymentTypeFilter,
    ExperienceLevelFilter,
    JobFilterChain,
    KeywordFilter,
    LocationFilter,
    RemoteFilter,
    SalaryRangeFilter,
)
from app.jobs.normalization import JobNormalizer
from app.jobs.providers.mock import MockJobProvider
from app.jobs.registry import JobProviderRegistry
from app.jobs.schemas import (
    CompanyInfo,
    EmploymentType,
    ExperienceLevel,
    JobPosting,
    JobSearchRequest,
    JobSearchResponse,
    LocationInfo,
    RemoteType,
    SalaryInfo,
)
from app.jobs.service import JobDiscoveryService


class TestSchemas:
    def test_job_posting_defaults(self):
        posting = JobPosting(title="Engineer", company=CompanyInfo(name="Acme"), provider="mock")
        assert posting.id is not None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.UNKNOWN
        assert posting.location.remote_type == RemoteType.UNKNOWN
        assert posting.skills == []

    def test_job_search_request_defaults(self):
        req = JobSearchRequest()
        assert req.limit == 25
        assert req.offset == 0
        assert req.deduplicate is True
        assert req.keywords == []

    def test_salary_info_validation(self):
        sal = SalaryInfo(min_amount=50000, max_amount=100000)
        assert sal.currency == "USD"
        assert sal.period == "yearly"

    def test_company_info_requires_name(self):
        with pytest.raises(Exception):
            CompanyInfo(name="")

    def test_job_search_response_defaults(self):
        resp = JobSearchResponse()
        assert resp.results == []
        assert resp.metadata.total_results == 0

    def test_employment_type_enum(self):
        assert EmploymentType.FULL_TIME.value == "full_time"
        assert EmploymentType.INTERNSHIP.value == "internship"

    def test_remote_type_enum(self):
        assert RemoteType.REMOTE.value == "remote"
        assert RemoteType.HYBRID.value == "hybrid"

    def test_experience_level_enum(self):
        assert ExperienceLevel.SENIOR.value == "senior"
        assert ExperienceLevel.ENTRY.value == "entry"


class TestJobProviderRegistry:
    def test_register_and_resolve(self):
        reg = JobProviderRegistry()
        cfg = JobDiscoveryConfig()
        provider = MockJobProvider(cfg)
        reg.register(provider)
        assert reg.resolve("mock") is provider

    def test_resolve_unknown_raises(self):
        reg = JobProviderRegistry()
        with pytest.raises(ProviderNotFoundError):
            reg.resolve("nope")

    def test_register_overwrite(self):
        reg = JobProviderRegistry()
        cfg = JobDiscoveryConfig()
        reg.register(MockJobProvider(cfg))
        reg.register(MockJobProvider(cfg))
        assert reg.count() == 1

    def test_unregister(self):
        reg = JobProviderRegistry()
        cfg = JobDiscoveryConfig()
        reg.register(MockJobProvider(cfg))
        reg.unregister("mock")
        assert reg.count() == 0

    def test_unregister_unknown_raises(self):
        reg = JobProviderRegistry()
        with pytest.raises(ProviderNotFoundError):
            reg.unregister("nope")

    def test_list_providers(self):
        reg = JobProviderRegistry()
        assert reg.list_providers() == []

    def test_is_registered(self):
        reg = JobProviderRegistry()
        cfg = JobDiscoveryConfig()
        assert not reg.is_registered("mock")
        reg.register(MockJobProvider(cfg))
        assert reg.is_registered("mock")

    def test_count(self):
        reg = JobProviderRegistry()
        cfg = JobDiscoveryConfig()
        assert reg.count() == 0
        reg.register(MockJobProvider(cfg))
        assert reg.count() == 1

    def test_clear(self):
        reg = JobProviderRegistry()
        cfg = JobDiscoveryConfig()
        reg.register(MockJobProvider(cfg))
        reg.clear()
        assert reg.count() == 0


class TestMockProvider:
    @pytest.fixture
    def config(self):
        return JobDiscoveryConfig()

    @pytest.fixture
    def provider(self, config):
        return MockJobProvider(config)

    async def test_search_jobs_returns_results(self, provider):
        request = JobSearchRequest(query="engineer")
        response = await provider.search_jobs(request)
        assert len(response.results) > 0
        assert response.metadata.total_results > 0

    async def test_search_jobs_returns_job_postings(self, provider):
        request = JobSearchRequest(query="engineer")
        response = await provider.search_jobs(request)
        for job in response.results:
            assert isinstance(job, JobPosting)
            assert job.title
            assert job.company.name
            assert job.provider == "mock"

    async def test_health_check(self, provider):
        result = await provider.health_check()
        assert result is True

    async def test_provider_info(self, provider):
        info = await provider.provider_info()
        assert info.name == "mock"
        assert info.display_name == "Mock Provider"
        assert info.is_available is True

    async def test_search_removes_duplicates(self, provider):
        request = JobSearchRequest(query="engineer", limit=50)
        response = await provider.search_jobs(request)
        urls = [j.url for j in response.results if j.url]
        assert len(urls) == len(set(urls))


class TestJobNormalizer:
    @pytest.fixture
    def normalizer(self):
        return JobNormalizer()

    def test_normalize_valid_data(self, normalizer):
        data = {
            "title": "  Software Engineer  ",
            "company": {"name": "Acme Corp", "industry": "Tech"},
            "description": "<p>Build <b>stuff</b></p>",
            "url": "https://example.com/job/1",
            "provider_job_id": "ext-001",
            "employment_type": "full_time",
            "experience_level": "Senior",
            "salary": {"min": 100000, "max": 150000},
            "skills": ["Python", "Docker"],
        }
        posting = normalizer.normalize(data, provider="test")
        assert posting.title == "Software Engineer"
        assert posting.company.name == "Acme Corp"
        assert posting.provider_job_id == "ext-001"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["Python", "Docker"]

    def test_normalize_employment_type_mapping(self, normalizer):
        assert normalizer._normalize_employment_type("contractor") == EmploymentType.CONTRACT
        assert normalizer._normalize_employment_type("full time") == EmploymentType.FULL_TIME
        assert normalizer._normalize_employment_type("intern") == EmploymentType.INTERNSHIP
        assert normalizer._normalize_employment_type(None) == EmploymentType.OTHER
        assert normalizer._normalize_employment_type("unknown_value") == EmploymentType.OTHER

    def test_normalize_experience_level_mapping(self, normalizer):
        assert normalizer._normalize_experience_level("sr") == ExperienceLevel.SENIOR
        assert normalizer._normalize_experience_level("entry level") == ExperienceLevel.ENTRY
        assert normalizer._normalize_experience_level("c_level") == ExperienceLevel.EXECUTIVE
        assert normalizer._normalize_experience_level(None) == ExperienceLevel.UNKNOWN

    def test_normalize_company_string(self, normalizer):
        data = {"title": "Dev", "company": "Startup Inc", "employee_type": "full_time"}
        posting = normalizer.normalize(data, provider="test")
        assert posting.company.name == "Startup Inc"

    def test_normalize_location_string(self, normalizer):
        data = {"title": "Dev", "company": {"name": "Co"}, "location": "Remote, US"}
        posting = normalizer.normalize(data, provider="test")
        assert posting.location.display_name == "Remote, US"

    def test_normalize_empty_title(self, normalizer):
        data = {"title": "", "company": {"name": "Co"}}
        posting = normalizer.normalize(data, provider="test")
        assert posting.title == "Untitled Position"

    def test_normalize_raises_on_bad_data(self, normalizer):
        with pytest.raises(NormalizationError):
            normalizer.normalize({"company": Exception("boom")}, provider="test")

    def test_clean_html_removes_tags(self, normalizer):
        cleaned = normalizer._clean_html("<p>Hello <b>World</b></p>")
        assert cleaned == "Hello World"


class TestDeduplication:
    @pytest.fixture
    def config(self):
        return JobDiscoveryConfig(dedup_by_url=True, dedup_by_provider_id=True)

    @pytest.fixture
    def engine(self, config):
        return DeduplicationEngine(config)

    def test_dedup_by_url(self, engine):
        jobs = [
            JobPosting(title="A", company=CompanyInfo(name="C"), url="https://x.com/1", provider="p1"),
            JobPosting(title="B", company=CompanyInfo(name="C"), url="https://x.com/1", provider="p2"),
        ]
        result = engine.deduplicate(jobs)
        assert len(result) == 1

    def test_dedup_by_provider_id(self, engine):
        jobs = [
            JobPosting(
                title="A", company=CompanyInfo(name="C"), provider_job_id="id-1", provider="p1"
            ),
            JobPosting(
                title="B", company=CompanyInfo(name="C"), provider_job_id="id-1", provider="p1"
            ),
        ]
        result = engine.deduplicate(jobs)
        assert len(result) == 1

    def test_dedup_no_duplicates(self, engine):
        jobs = [
            JobPosting(
                title="A", company=CompanyInfo(name="C1"), url="https://x.com/1", provider="p1"
            ),
            JobPosting(
                title="B", company=CompanyInfo(name="C2"), url="https://x.com/2", provider="p2"
            ),
        ]
        result = engine.deduplicate(jobs)
        assert len(result) == 2

    def test_dedup_empty_list(self, engine):
        result = engine.deduplicate([])
        assert result == []

    def test_dedup_url_normalization(self, engine):
        jobs = [
            JobPosting(title="A", company=CompanyInfo(name="C"), url="https://X.com/Path/", provider="p1"),
            JobPosting(title="A", company=CompanyInfo(name="C"), url="https://x.com/path", provider="p2"),
        ]
        result = engine.deduplicate(jobs)
        assert len(result) == 1

    def test_dedup_title_company_location(self):
        config = JobDiscoveryConfig(
            dedup_by_url=False,
            dedup_by_provider_id=False,
            dedup_by_title_company_location=True,
        )
        engine = DeduplicationEngine(config)
        jobs = [
            JobPosting(
                title="Engineer",
                company=CompanyInfo(name="Acme"),
                location=LocationInfo(city="NYC"),
                provider="p1",
            ),
            JobPosting(
                title="Engineer",
                company=CompanyInfo(name="Acme"),
                location=LocationInfo(city="NYC"),
                provider="p2",
            ),
        ]
        result = engine.deduplicate(jobs)
        assert len(result) == 1

    def test_dedup_no_key_falls_back(self, engine):
        jobs = [
            JobPosting(title="A", company=CompanyInfo(name="C"), provider="p1"),
            JobPosting(title="B", company=CompanyInfo(name="C"), provider="p2"),
        ]
        result = engine.deduplicate(jobs)
        assert len(result) == 2


class TestFilters:
    def test_keyword_filter_matches_title(self):
        jobs = [
            JobPosting(title="Software Engineer", company=CompanyInfo(name="Acme"), provider="p1"),
            JobPosting(title="Product Manager", company=CompanyInfo(name="Acme"), provider="p1"),
        ]
        f = KeywordFilter(["Engineer"])
        result = f.apply(jobs)
        assert len(result) == 1
        assert result[0].title == "Software Engineer"

    def test_keyword_filter_empty_returns_all(self):
        jobs = [
            JobPosting(title="Engineer", company=CompanyInfo(name="Acme"), provider="p1"),
        ]
        f = KeywordFilter([])
        result = f.apply(jobs)
        assert len(result) == 1

    def test_location_filter(self):
        jobs = [
            JobPosting(
                title="A",
                company=CompanyInfo(name="C"),
                location=LocationInfo(city="San Francisco"),
                provider="p1",
            ),
            JobPosting(
                title="B",
                company=CompanyInfo(name="C"),
                location=LocationInfo(city="New York"),
                provider="p1",
            ),
        ]
        f = LocationFilter("San Francisco")
        result = f.apply(jobs)
        assert len(result) == 1
        assert result[0].title == "A"

    def test_location_filter_partial_match(self):
        jobs = [
            JobPosting(
                title="A",
                company=CompanyInfo(name="C"),
                location=LocationInfo(city="San Francisco"),
                provider="p1",
            ),
        ]
        f = LocationFilter("francisco")
        result = f.apply(jobs)
        assert len(result) == 1

    def test_remote_filter(self):
        jobs = [
            JobPosting(
                title="A",
                company=CompanyInfo(name="C"),
                location=LocationInfo(remote_type=RemoteType.REMOTE),
                provider="p1",
            ),
            JobPosting(
                title="B",
                company=CompanyInfo(name="C"),
                location=LocationInfo(remote_type=RemoteType.ON_SITE),
                provider="p1",
            ),
        ]
        f = RemoteFilter(True)
        result = f.apply(jobs)
        assert len(result) == 1
        assert result[0].title == "A"

    def test_remote_filter_disabled(self):
        jobs = [JobPosting(title="A", company=CompanyInfo(name="C"), provider="p1")]
        f = RemoteFilter(False)
        result = f.apply(jobs)
        assert len(result) == 1

    def test_experience_level_filter(self):
        jobs = [
            JobPosting(title="A", company=CompanyInfo(name="C"),
                       experience_level=ExperienceLevel.SENIOR, provider="p1"),
            JobPosting(title="B", company=CompanyInfo(name="C"),
                       experience_level=ExperienceLevel.JUNIOR, provider="p1"),
        ]
        f = ExperienceLevelFilter(ExperienceLevel.SENIOR)
        result = f.apply(jobs)
        assert len(result) == 1
        assert result[0].title == "A"

    def test_employment_type_filter(self):
        jobs = [
            JobPosting(title="A", company=CompanyInfo(name="C"),
                       employment_type=EmploymentType.FULL_TIME, provider="p1"),
            JobPosting(title="B", company=CompanyInfo(name="C"),
                       employment_type=EmploymentType.INTERNSHIP, provider="p1"),
        ]
        f = EmploymentTypeFilter(EmploymentType.INTERNSHIP)
        result = f.apply(jobs)
        assert len(result) == 1
        assert result[0].title == "B"

    def test_salary_range_filter_both(self):
        jobs = [
            JobPosting(
                title="A",
                company=CompanyInfo(name="C"),
                salary=SalaryInfo(min_amount=50000, max_amount=100000),
                provider="p1",
            ),
            JobPosting(
                title="B",
                company=CompanyInfo(name="C"),
                salary=SalaryInfo(min_amount=150000, max_amount=200000),
                provider="p1",
            ),
        ]
        f = SalaryRangeFilter(min_amount=80000, max_amount=120000)
        result = f.apply(jobs)
        assert len(result) == 1
        assert result[0].title == "A"

    def test_salary_range_filter_min_only(self):
        jobs = [
            JobPosting(
                title="A",
                company=CompanyInfo(name="C"),
                salary=SalaryInfo(min_amount=50000),
                provider="p1",
            ),
            JobPosting(
                title="B",
                company=CompanyInfo(name="C"),
                salary=SalaryInfo(min_amount=150000),
                provider="p1",
            ),
        ]
        f = SalaryRangeFilter(min_amount=100000, max_amount=None)
        result = f.apply(jobs)
        assert len(result) == 1
        assert result[0].title == "B"

    def test_filter_chain_from_request(self):
        request = JobSearchRequest(
            keywords=["Python"],
            location="Remote",
            remote_only=True,
            salary_min=100000,
        )
        chain = JobFilterChain.from_request(request)
        assert len(chain._filters) == 4

    def test_filter_chain_empty_request(self):
        request = JobSearchRequest()
        chain = JobFilterChain.from_request(request)
        assert chain._filters == []


class TestJobDiscoveryService:
    @pytest.fixture
    def config(self):
        return JobDiscoveryConfig(enabled_providers=["mock"])

    @pytest.fixture
    def registry(self):
        reg = JobProviderRegistry()
        reg.register(MockJobProvider(JobDiscoveryConfig()))
        return reg

    @pytest.fixture
    def service(self, registry, config):
        return JobDiscoveryService(registry=registry, config=config)

    async def test_search_returns_results(self, service):
        response = await service.search(JobSearchRequest(query="engineer"))
        assert len(response.results) > 0
        assert response.metadata.total_results > 0
        assert "mock" in response.metadata.providers_queried

    async def test_search_validates_request(self, service):
        with pytest.raises(SearchValidationError):
            await service.search(JobSearchRequest())

    async def test_search_deduplicates(self, service):
        response = await service.search(JobSearchRequest(query="engineer", limit=50))
        urls = [j.url for j in response.results if j.url]
        assert len(urls) == len(set(urls))

    async def test_search_filters_by_keywords(self, service):
        response = await service.search(JobSearchRequest(query="Python"))
        for job in response.results:
            text = f"{job.title} {job.company.name} {job.description or ''}".lower()
            assert "python" in text

    async def test_search_remote_only(self, service):
        response = await service.search(JobSearchRequest(query="engineer", remote_only=True))
        for job in response.results:
            assert job.location.remote_type == RemoteType.REMOTE

    async def test_search_with_pagination(self, service):
        response = await service.search(JobSearchRequest(query="engineer", limit=2))
        assert len(response.results) <= 2

    async def test_search_with_specific_provider(self, service):
        response = await service.search(JobSearchRequest(query="engineer", providers=["mock"]))
        assert len(response.results) > 0

    async def test_search_with_invalid_provider_raises(self, service):
        with pytest.raises(ProviderNotFoundError):
            await service.search(JobSearchRequest(query="engineer", providers=["nonexistent"]))

    async def test_health_check(self, service):
        result = await service.health_check("mock")
        assert result == {"mock": True}

    async def test_health_check_unknown_provider(self, service):
        result = await service.health_check("nope")
        assert result == {"nope": False}

    async def test_list_providers(self, service):
        providers = service.list_providers()
        assert "mock" in providers

    async def test_provider_info(self, service):
        info = await service.provider_info("mock")
        assert info.name == "mock"
        assert info.is_available is True

    async def test_search_applies_deduplication(self, service):
        request = JobSearchRequest(query="engineer", deduplicate=True, limit=50)
        response = await service.search(request)
        assert response.metadata.duplicates_removed == 0

    async def test_search_deduplicate_disabled(self, service):
        request = JobSearchRequest(query="engineer", deduplicate=False, limit=50)
        response = await service.search(request)
        assert response.metadata.duplicates_removed == 0

    async def test_search_metadata_has_duration(self, service):
        response = await service.search(JobSearchRequest(query="engineer"))
        assert response.metadata.duration_ms is not None
        assert response.metadata.duration_ms >= 0

    async def test_search_metadata_providers(self, service):
        response = await service.search(JobSearchRequest(query="engineer"))
        assert "mock" in response.metadata.providers_succeeded

    async def test_search_filters_applied_listed(self, service):
        response = await service.search(JobSearchRequest(query="Python", remote_only=True))
        assert "keyword" in response.metadata.filters_applied
        assert "remote" in response.metadata.filters_applied


class TestExceptions:
    def test_job_discovery_error_hierarchy(self):
        from app.core.exceptions import AppError
        from app.jobs.exceptions import JobDiscoveryError

        assert issubclass(JobDiscoveryError, AppError)

    def test_provider_not_found(self):
        err = ProviderNotFoundError("test")
        assert err.status_code == 404
        assert "test" in str(err)

    def test_search_validation_error(self):
        err = SearchValidationError()
        assert err.status_code == 400

    def test_normalization_error(self):
        err = NormalizationError()
        assert err.code == "NORMALIZATION_ERROR"


class TestConfig:
    def test_default_values(self):
        config = JobDiscoveryConfig()
        assert config.request_timeout_seconds == 30
        assert config.retry_count == 2
        assert config.default_search_limit == 25
        assert config.dedup_by_url is True

    def test_custom_values(self):
        config = JobDiscoveryConfig(
            enabled_providers=["mock", "linkedin"],
            request_timeout_seconds=60,
            retry_count=5,
            default_search_limit=50,
            dedup_by_url=False,
        )
        assert config.enabled_providers == ["mock", "linkedin"]
        assert config.request_timeout_seconds == 60
        assert config.retry_count == 5
        assert config.default_search_limit == 50

    def test_validation(self):
        with pytest.raises(Exception):
            JobDiscoveryConfig(default_search_limit=200)
