from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.jobs.config import (
    AshbyConfig,
    GreenhouseConfig,
    JobDiscoveryConfig,
    LeverConfig,
    WellfoundConfig,
    YCombinatorConfig,
)
from app.jobs.exceptions import ProviderUnavailableError
from app.jobs.providers.ashby import AshbyJobProvider
from app.jobs.providers.greenhouse import GreenhouseJobProvider
from app.jobs.providers.lever import LeverJobProvider
from app.jobs.providers.wellfound import WellfoundJobProvider
from app.jobs.providers.y_combinator import YCombinatorJobProvider
from app.jobs.schemas import (
    EmploymentType,
    ExperienceLevel,
    JobProviderInfo,
    JobSearchRequest,
    RemoteType,
)


def make_config(**overrides) -> JobDiscoveryConfig:
    return JobDiscoveryConfig(**overrides)


class TestConfigDefaults:
    def test_wellfound_config_defaults(self):
        c = WellfoundConfig()
        assert c.base_url == "https://api.angel.co/1"
        assert c.page_size == 20
        assert c.rate_limit_rate == 10.0
        assert c.rate_limit_burst == 5

    def test_y_combinator_config_defaults(self):
        c = YCombinatorConfig()
        assert c.base_url == "https://www.workatastartup.com"
        assert c.page_size == 20

    def test_greenhouse_config_defaults(self):
        c = GreenhouseConfig()
        assert c.base_url == "https://boards-api.greenhouse.io/v1/boards"
        assert c.page_size == 20

    def test_lever_config_defaults(self):
        c = LeverConfig()
        assert c.base_url == "https://api.lever.co/v0"
        assert c.page_size == 20

    def test_ashby_config_defaults(self):
        c = AshbyConfig()
        assert c.base_url == "https://api.ashbyhq.com/posting-api"
        assert c.page_size == 20


class TestWellfoundJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["wellfound"])

    @pytest.fixture
    def provider(self, config):
        return WellfoundJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "wellfound"
        assert provider.display_name == "Wellfound"
        assert provider.supports_pagination is True
        assert provider.supports_filters is True

    def test_build_search_params_query(self, provider):
        request = JobSearchRequest(query="engineer", location="San Francisco")
        params = provider._build_search_params(request)
        assert params["query"] == "engineer"
        assert params["location"] == "San Francisco"
        assert params["per_page"] == 25

    def test_build_search_params_remote(self, provider):
        request = JobSearchRequest(query="engineer", remote_only=True)
        params = provider._build_search_params(request)
        assert params["remote"] == "true"

    def test_build_search_params_keywords(self, provider):
        request = JobSearchRequest(keywords=["python", "django"])
        params = provider._build_search_params(request)
        assert params["query"] == "python django"

    def test_parse_response(self, provider):
        data = {
            "total": 2,
            "jobs": [
                {
                    "id": "wf-1",
                    "title": "Full Stack Engineer",
                    "startup": {"name": "StartupCo"},
                    "locations": [{"display_name": "San Francisco, CA"}],
                    "description": "Build awesome stuff",
                    "salary_min": 120000,
                    "salary_max": 160000,
                    "job_type": "full-time",
                },
            ],
        }
        request = JobSearchRequest(query="engineer")
        response = provider._parse_response(data, request)
        assert len(response.results) == 1
        assert response.results[0].title == "Full Stack Engineer"
        assert response.results[0].company.name == "StartupCo"

    def test_parse_response_empty(self, provider):
        data = {"total": 0, "jobs": []}
        response = provider._parse_response(data, JobSearchRequest(query="nothing"))
        assert len(response.results) == 0

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "wf-42",
            "title": "Senior Backend Engineer",
            "startup": {"name": "TechStars", "product_desc": "AI platform"},
            "locations": [{"display_name": "New York, NY"}],
            "description": "Build APIs",
            "url": "https://angel.co/jobs/42",
            "salary_min": 150000,
            "salary_max": 200000,
            "salary_currency": "USD",
            "job_type": "full-time",
            "tags": ["python", "go"],
            "created_at": "2024-06-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "wf-42"
        assert posting.title == "Senior Backend Engineer"
        assert posting.company.name == "TechStars"
        assert posting.company.description == "AI platform"
        assert posting.location.display_name == "New York, NY"
        assert posting.salary is not None
        assert posting.salary.min_amount == 150000
        assert posting.salary.max_amount == 200000
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["python", "go"]

    def test_raw_to_posting_minimal(self, provider):
        raw = {"id": "1", "title": "Dev"}
        posting = provider._raw_to_posting(raw)
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_parse_location_from_locations(self, provider):
        raw = {"locations": [{"display_name": "Remote, US"}], "remote": True}
        loc = provider._parse_location(raw)
        assert loc.display_name == "Remote, US"
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_location_fallback(self, provider):
        raw = {"location": "Austin, TX"}
        loc = provider._parse_location(raw)
        assert loc.display_name == "Austin, TX"
        assert loc.remote_type == RemoteType.ON_SITE

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salary_min": 50000, "salary_max": 100000})
        assert sal is not None
        assert sal.min_amount == 50000
        assert sal.max_amount == 100000

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"job_type": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"job_type": "internship"}) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({"job_type": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"job_type": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"job_type": "unknown"}) == EmploymentType.OTHER
        assert provider._normalize_employment({"equity_possible": True}) == EmploymentType.FULL_TIME

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Senior Engineer", {}) == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Developer", {}) == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Intern", {}) == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Engineer", {}) == ExperienceLevel.MID
        assert provider._normalize_experience("Sr. Architect", {}) == ExperienceLevel.SENIOR

    async def test_search_jobs_integration(self, provider):
        mock_data = {
            "total": 1,
            "jobs": [
                {
                    "id": "1",
                    "title": "Software Engineer",
                    "startup": {"name": "Co"},
                    "description": "desc",
                },
            ],
        }
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="engineer"))
            assert len(response.results) == 1
            assert response.results[0].title == "Software Engineer"

    async def test_health_check_success(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"total": 0, "jobs": []})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"total": 0, "jobs": []})):
            info = await provider.provider_info()
            assert info.name == "wellfound"
            assert info.is_available is True
            assert isinstance(info, JobProviderInfo)


class TestYCombinatorJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["y_combinator"])

    @pytest.fixture
    def provider(self, config):
        return YCombinatorJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "y_combinator"
        assert provider.display_name == "Y Combinator"

    def test_build_search_params_query(self, provider):
        request = JobSearchRequest(query="engineer", location="SF")
        params = provider._build_search_params(request)
        assert params["query"] == "engineer"
        assert params["location"] == "SF"
        assert params["limit"] == 25

    def test_build_search_params_remote(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="dev", remote_only=True))
        assert params["remote"] == "true"

    def test_parse_response(self, provider):
        data = {
            "total": 1,
            "jobs": [
                {
                    "id": "yc-1",
                    "title": "Frontend Engineer",
                    "company": {"name": "YC Startup"},
                    "location": "Palo Alto, CA",
                    "description": "Build UI",
                },
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 1
        assert response.results[0].company.name == "YC Startup"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({"total": 0, "jobs": []}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "yc-42",
            "title": "Senior Data Scientist",
            "company": {
                "name": "AI Labs",
                "description": "ML for everyone",
                "team_size": 50,
                "url": "https://ailabs.com",
            },
            "location": "Remote, US",
            "description": "Build ML models",
            "url": "https://workatastartup.com/jobs/42",
            "salary_min": 180000,
            "salary_max": 250000,
            "salary_currency": "USD",
            "job_type": "full-time",
            "skills": ["python", "ml"],
            "created_at": "2024-07-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "yc-42"
        assert posting.title == "Senior Data Scientist"
        assert posting.company.name == "AI Labs"
        assert posting.company.description == "ML for everyone"
        assert posting.company.size == "50"
        assert posting.company.website == "https://ailabs.com"
        assert posting.salary.min_amount == 180000
        assert posting.salary.max_amount == 250000
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["python", "ml"]

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.FULL_TIME

    def test_parse_location_string(self, provider):
        loc = provider._parse_location({"location": "Mountain View, CA"})
        assert loc.display_name == "Mountain View, CA"
        assert loc.remote_type == RemoteType.ON_SITE

    def test_parse_location_list(self, provider):
        loc = provider._parse_location({"locations": ["SF", "NYC"], "remote": True})
        assert loc.display_name == "SF, NYC"
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salary_min": 60000, "salary_max": 120000})
        assert sal is not None
        assert sal.min_amount == 60000
        assert sal.max_amount == 120000

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"job_type": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"job_type": "internship"}) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({"job_type": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"job_type": "part-time"}) == EmploymentType.PART_TIME

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Lead Developer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Jr. Engineer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Intern") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Software Engineer") == ExperienceLevel.MID

    async def test_search_jobs_integration(self, provider):
        mock_data = {"total": 1, "jobs": [{"id": "1", "title": "Dev", "company": {"name": "C"}}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="dev"))
            assert len(response.results) == 1

    async def test_health_check(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"total": 0, "jobs": []})):
            assert await provider.health_check() is True


class TestGreenhouseJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["greenhouse"])

    @pytest.fixture
    def provider(self, config):
        return GreenhouseJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "greenhouse"
        assert provider.display_name == "Greenhouse"

    def test_build_search_params(self, provider):
        request = JobSearchRequest(query="engineer", location="NYC")
        params = provider._build_search_params(request)
        assert params["query"] == "engineer"
        assert params["location"] == "NYC"
        assert params["per_page"] == 25

    def test_parse_response(self, provider):
        data = {
            "jobs": [
                {
                    "id": 101,
                    "title": "Software Engineer",
                    "location": {"name": "New York, NY"},
                    "absolute_url": "https://boards.greenhouse.io/jobs/101",
                    "metadata": {"fields": []},
                },
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 1
        assert response.results[0].title == "Software Engineer"
        assert response.results[0].location.display_name == "New York, NY"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({"jobs": []}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": 42,
            "title": "Senior Product Manager",
            "company": {"name": "BigCo"},
            "offices": [{"name": "San Francisco, CA"}],
            "content": "Lead product strategy",
            "absolute_url": "https://boards.greenhouse.io/jobs/42",
            "board_token": "bigco",
            "metadata": {
                "fields": [
                    {"name": "Employment Type", "value": "Full-time"},
                    {"name": "Salary", "value": "$150,000 - $200,000"},
                ],
            },
            "updated_at": "2024-08-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "42"
        assert posting.title == "Senior Product Manager"
        assert posting.company.name == "BigCo"
        assert posting.location.display_name == "San Francisco, CA"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.salary is not None

    def test_raw_to_posting_minimal(self, provider):
        raw = {"id": 1, "title": "Engineer"}
        posting = provider._raw_to_posting(raw)
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_parse_location_with_offices(self, provider):
        loc = provider._parse_location({}, [{"name": "Remote"}])
        assert loc.display_name == "Remote"
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_location_from_raw(self, provider):
        loc = provider._parse_location({"location": {"name": "Chicago, IL"}}, [])
        assert loc.display_name == "Chicago, IL"
        assert loc.remote_type == RemoteType.ON_SITE

    def _md_fields(self, v: str) -> dict:
        return {"fields": [{"name": "Employment Type", "value": v}]}

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment(self._md_fields("Full-time")) == EmploymentType.FULL_TIME
        assert provider._normalize_employment(self._md_fields("Part-time")) == EmploymentType.PART_TIME
        assert provider._normalize_employment(self._md_fields("Contract")) == EmploymentType.CONTRACT
        assert provider._normalize_employment(self._md_fields("Internship")) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Principal Engineer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior QA") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Director of Eng") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Intern") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Software Developer") == ExperienceLevel.MID

    async def test_search_jobs_integration(self, provider):
        mock_data = {
            "jobs": [
                {"id": 1, "title": "Dev", "metadata": {"fields": []}},
            ],
        }
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="dev"))
            assert len(response.results) == 1

    async def test_health_check(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": []})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": []})):
            info = await provider.provider_info()
            assert info.name == "greenhouse"
            assert info.is_available is True


class TestLeverJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["lever"])

    @pytest.fixture
    def provider(self, config):
        return LeverJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "lever"
        assert provider.display_name == "Lever"

    def test_build_search_params(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="developer"))
        assert params["query"] == "developer"
        assert params["limit"] == 25
        assert params["mode"] == "json"
        assert params["group"] == "team"

    def test_parse_response(self, provider):
        data = {
            "data": [
                {
                    "id": "lev-1",
                    "text": "Backend Engineer",
                    "company": {"name": "LeverCo"},
                    "location": "San Francisco, CA",
                    "applyUrl": "https://jobs.lever.co/lev-1",
                },
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 1
        assert response.results[0].title == "Backend Engineer"
        assert response.results[0].company.name == "LeverCo"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "lev-42",
            "text": "Senior Frontend Engineer",
            "company": {"name": "UI Corp"},
            "location": "Remote, US",
            "descriptionPlain": "Build UIs",
            "applyUrl": "https://jobs.lever.co/lev-42",
            "categories": {
                "commitment": "full-time",
                "salary": "$160,000 - $220,000",
                "team": "Engineering",
            },
            "lists": [
                {"items": [{"content": "React"}, {"content": "TypeScript"}]},
            ],
            "createdAt": "2024-09-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "lev-42"
        assert posting.title == "Senior Frontend Engineer"
        assert posting.company.name == "UI Corp"
        assert posting.location.display_name == "Remote, US"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.salary is not None
        assert posting.salary.min_amount == 160000
        assert posting.salary.max_amount == 220000
        assert "React" in posting.skills
        assert "TypeScript" in posting.skills

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "text": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER

    def test_parse_location_dict(self, provider):
        loc = provider._parse_location({"location": {"name": "Austin, TX"}})
        assert loc.display_name == "Austin, TX"

    def test_parse_location_string(self, provider):
        loc = provider._parse_location({"location": "New York, NY"})
        assert loc.display_name == "New York, NY"

    def test_parse_salary_from_categories(self, provider):
        raw = {"categories": {"salary": "$100,000 - $150,000"}}
        sal = provider._parse_salary(raw)
        assert sal is not None
        assert sal.min_amount == 100000
        assert sal.max_amount == 150000

    def test_parse_salary_direct(self, provider):
        raw = {"salaryLow": 80000, "salaryHigh": 120000}
        sal = provider._parse_salary(raw)
        assert sal is not None
        assert sal.min_amount == 80000
        assert sal.max_amount == 120000

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"commitment": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"commitment": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"commitment": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Staff Engineer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Developer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("VP Engineering") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Trainee") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Software Engineer") == ExperienceLevel.MID

    async def test_search_jobs_integration(self, provider):
        mock_data = {"data": [{"id": "1", "text": "Dev"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="dev"))
            assert len(response.results) == 1

    async def test_health_check(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"data": []})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"data": []})):
            info = await provider.provider_info()
            assert info.name == "lever"
            assert info.is_available is True


class TestAshbyJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["ashby"])

    @pytest.fixture
    def provider(self, config):
        return AshbyJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "ashby"
        assert provider.display_name == "Ashby"

    def test_build_search_params(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="engineer", location="SF"))
        assert params["search"] == "engineer"
        assert params["location"] == "SF"

    def test_build_search_params_keywords(self, provider):
        params = provider._build_search_params(JobSearchRequest(keywords=["python"]))
        assert params["search"] == "python"

    def test_parse_response(self, provider):
        data = {
            "jobs": [
                {
                    "id": "ash-1",
                    "title": "Data Engineer",
                    "organization": {"name": "AshbyCo"},
                    "location": {"city": "Chicago", "state": "IL"},
                    "url": "https://jobs.ashbyhq.com/ash-1",
                },
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 1
        assert response.results[0].title == "Data Engineer"
        assert response.results[0].company.name == "AshbyCo"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_parse_response_slicing(self, provider):
        data = {"jobs": [{"id": str(i), "title": f"Job {i}"} for i in range(10)]}
        request = JobSearchRequest(query="job", offset=5, limit=3)
        response = provider._parse_response(data, request)
        assert len(response.results) == 3
        assert response.results[0].title == "Job 5"

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "ash-42",
            "title": "Senior DevOps Engineer",
            "organization": {"name": "CloudCo", "description": "Cloud infra"},
            "location": {"city": "Seattle", "state": "WA", "country": "US"},
            "descriptionHtml": "Manage infrastructure",
            "url": "https://jobs.ashbyhq.com/ash-42",
            "salary": {"min": 170000, "max": 230000, "currency": "USD"},
            "employmentType": "full-time",
            "skills": ["kubernetes", "terraform"],
            "publishedDate": "2024-10-01T00:00:00Z",
            "isRemote": True,
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "ash-42"
        assert posting.title == "Senior DevOps Engineer"
        assert posting.company.name == "CloudCo"
        assert posting.company.description == "Cloud infra"
        assert posting.location.display_name == "Seattle, WA, US"
        assert posting.location.remote_type == RemoteType.REMOTE
        assert posting.salary is not None
        assert posting.salary.min_amount == 170000
        assert posting.salary.max_amount == 230000
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["kubernetes", "terraform"]

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_parse_location_dict(self, provider):
        loc = provider._parse_location({"location": {"city": "Boston", "state": "MA", "country": "US"}})
        assert loc.display_name == "Boston, MA, US"

    def test_parse_location_string_fallback(self, provider):
        loc = provider._parse_location({"location": "Denver, CO"})
        assert loc.display_name == "Denver, CO"

    def test_parse_salary_from_dict(self, provider):
        sal = provider._parse_salary({"salary": {"min": 90000, "max": 130000}})
        assert sal is not None
        assert sal.min_amount == 90000
        assert sal.max_amount == 130000

    def test_parse_salary_from_string(self, provider):
        sal = provider._parse_salary({"salaryRange": "$80,000 - $120,000"})
        assert sal is not None
        assert sal.min_amount == 80000
        assert sal.max_amount == 120000

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"employmentType": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"employmentType": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "internship"}) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({"employmentType": "freelance"}) == EmploymentType.FREELANCE
        assert provider._normalize_employment({"employmentType": "temp"}) == EmploymentType.TEMPORARY
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Head of Engineering") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Analyst") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Chief Architect") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Entry Level Developer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Marketing Manager") == ExperienceLevel.MID

    async def test_search_jobs_integration(self, provider):
        mock_data = {"jobs": [{"id": "1", "title": "Dev"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="dev"))
            assert len(response.results) == 1

    async def test_health_check(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": []})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": []})):
            info = await provider.provider_info()
            assert info.name == "ashby"
            assert info.is_available is True


class TestFactoryRegistrations:
    def test_register_wellfound(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["wellfound"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "wellfound" in names

    def test_register_y_combinator(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["y_combinator"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "y_combinator" in names

    def test_register_greenhouse(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["greenhouse"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "greenhouse" in names

    def test_register_lever(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["lever"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "lever" in names

    def test_register_ashby(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["ashby"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "ashby" in names

    def test_register_all_five(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["wellfound", "y_combinator", "greenhouse", "lever", "ashby"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        for n in ("wellfound", "y_combinator", "greenhouse", "lever", "ashby"):
            assert n in names

    def test_skip_when_not_enabled(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=[])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "wellfound" not in names
        assert "greenhouse" not in names


class TestPhase3Config:
    def test_job_discovery_config_with_all(self):
        config = make_config(
            enabled_providers=["wellfound", "y_combinator", "greenhouse", "lever", "ashby"],
            wellfound=WellfoundConfig(base_url="https://custom.angel.co"),
            greenhouse=GreenhouseConfig(page_size=50),
        )
        assert config.wellfound.base_url == "https://custom.angel.co"
        assert config.greenhouse.page_size == 50

    def test_page_size_validation(self):
        with pytest.raises(Exception):
            WellfoundConfig(page_size=0)
        with pytest.raises(Exception):
            GreenhouseConfig(page_size=100)
        with pytest.raises(Exception):
            LeverConfig(page_size=-1)
        with pytest.raises(Exception):
            AshbyConfig(page_size=0)
