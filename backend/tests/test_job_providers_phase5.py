from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.jobs.config import (
    BambooHRConfig,
    JobDiscoveryConfig,
    RecruiteeConfig,
    SmartRecruitersConfig,
    WorkdayConfig,
)
from app.jobs.exceptions import ProviderUnavailableError
from app.jobs.providers.bamboohr import BambooHRJobProvider
from app.jobs.providers.recruitee import RecruiteeJobProvider
from app.jobs.providers.smartrecruiters import SmartRecruitersJobProvider
from app.jobs.providers.workday import WorkdayJobProvider
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
    def test_workday_config_defaults(self):
        c = WorkdayConfig()
        assert c.base_url == "https://wd5.myworkdayjobs.com/wday/cxs"
        assert c.page_size == 20
        assert c.rate_limit_rate == 5.0
        assert c.rate_limit_burst == 3
        assert c.tenant == "default"

    def test_smartrecruiters_config_defaults(self):
        c = SmartRecruitersConfig()
        assert c.base_url == "https://api.smartrecruiters.com/v1"
        assert c.page_size == 20
        assert c.rate_limit_rate == 10.0
        assert c.rate_limit_burst == 5
        assert c.company_id == "default"

    def test_bamboohr_config_defaults(self):
        c = BambooHRConfig()
        assert c.base_url == "https://api.bamboohr.com/api/gateway.php"
        assert c.page_size == 20
        assert c.rate_limit_rate == 5.0
        assert c.rate_limit_burst == 3
        assert c.company_subdomain == "default"

    def test_recruitee_config_defaults(self):
        c = RecruiteeConfig()
        assert c.base_url == "https://api.recruitee.com/c"
        assert c.page_size == 20
        assert c.rate_limit_rate == 10.0
        assert c.rate_limit_burst == 5
        assert c.company_id == "default"


class TestWorkdayJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["workday"])

    @pytest.fixture
    def provider(self, config):
        return WorkdayJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "workday"
        assert provider.display_name == "Workday"
        assert provider.supports_pagination is True
        assert provider.supports_filters is True

    def test_build_search_params_query(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="engineer", location="Chicago"))
        assert params["search"] == "engineer"
        assert params["location"] == "Chicago"
        assert "limit" in params

    def test_build_search_params_keywords(self, provider):
        params = provider._build_search_params(JobSearchRequest(keywords=["python", "django"]))
        assert params["search"] == "python django"

    def test_build_search_params_no_query(self, provider):
        params = provider._build_search_params(JobSearchRequest(location="Austin"))
        assert "search" not in params
        assert params["location"] == "Austin"



    def test_parse_response(self, provider):
        data = {
            "total": 2,
            "jobPostings": [
                {"id": "wd-1", "title": "Engineer", "company": {"name": "Acme"}, "location": "Chicago, IL"},
                {"id": "wd-2", "title": "Designer", "company": {"name": "Acme"}, "location": "Remote"},
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 2
        assert response.results[0].title == "Engineer"
        assert response.results[0].company.name == "Acme"
        assert response.metadata.total_results == 2

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({"total": 0, "jobPostings": []}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_parse_response_aliases(self, provider):
        data = {"totalCount": 1, "jobs": [{"id": "1", "title": "Dev", "companyName": "Startup"}]}
        response = provider._parse_response(data, JobSearchRequest(query="dev"))
        assert len(response.results) == 1

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "wd-42",
            "title": "Senior Software Engineer",
            "company": {"name": "AcmeCorp", "description": "Cloud platform"},
            "location": {"city": "San Francisco", "state": "CA", "country": "United States"},
            "description": "Build cloud infrastructure",
            "url": "https://acme.wd5.myworkdayjobs.com/job/42",
            "salaryMin": 150000,
            "salaryMax": 200000,
            "salaryCurrency": "USD",
            "employmentType": "full-time",
            "skills": ["python", "aws"],
            "postedDate": "2025-01-15T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "wd-42"
        assert posting.title == "Senior Software Engineer"
        assert posting.company.name == "AcmeCorp"
        assert posting.company.description is None
        assert posting.location.display_name == "San Francisco, CA, United States"
        assert posting.description == "Build cloud infrastructure"
        assert posting.url == "https://acme.wd5.myworkdayjobs.com/job/42"
        assert posting.apply_url == posting.url
        assert posting.salary is not None
        assert posting.salary.min_amount == 150000
        assert posting.salary.max_amount == 200000
        assert posting.salary.currency == "USD"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["python", "aws"]
        assert posting.posted_date == datetime(2025, 1, 15, tzinfo=timezone.utc)
        assert posting.provider == "workday"

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID
        assert posting.location.display_name == ""
        assert posting.skills == []

    def test_parse_location_dict(self, provider):
        loc = provider._parse_location({"location": {"city": "New York", "state": "NY", "country": "US"}})
        assert loc.display_name == "New York, NY, US"
        assert loc.remote_type == RemoteType.ON_SITE

    def test_parse_location_string(self, provider):
        loc = provider._parse_location({"location": "Austin, TX"})
        assert loc.display_name == "Austin, TX"
        assert loc.remote_type == RemoteType.ON_SITE

    def test_parse_location_list(self, provider):
        loc = provider._parse_location({"location": ["San Francisco", "Oakland"]})
        assert "San Francisco" in loc.display_name

    def test_parse_location_remote(self, provider):
        loc = provider._parse_location({"location": "Remote", "remote": True})
        assert loc.display_name == "Remote"
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_location_is_remote(self, provider):
        loc = provider._parse_location({"location": "Home", "isRemote": True})
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_location_work_from_home(self, provider):
        loc = provider._parse_location({"location": "Home", "workFromHome": True})
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salaryMin": 100000, "salaryMax": 150000})
        assert sal is not None
        assert sal.min_amount == 100000
        assert sal.max_amount == 150000
        assert sal.currency == "USD"

    def test_parse_salary_aliases(self, provider):
        sal = provider._parse_salary({"minSalary": 80000, "maxSalary": 120000})
        assert sal is not None
        assert sal.min_amount == 80000
        assert sal.max_amount == 120000

    def test_parse_salary_string(self, provider):
        sal = provider._parse_salary({"salaryRange": "$100,000 - $150,000"})
        assert sal is not None
        assert sal.min_amount == 100000
        assert sal.max_amount == 150000

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"employmentType": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"employmentType": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "internship"}) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({"employmentType": "temporary"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "temp"}) == EmploymentType.TEMPORARY
        assert provider._normalize_employment({"employmentType": "permanent"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "regular"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_employment_dict_type(self, provider):
        assert provider._normalize_employment({"employmentType": {"name": "Full-Time"}}) == EmploymentType.FULL_TIME

    def test_normalize_employment_type_alias(self, provider):
        assert provider._normalize_employment({"type": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"employment_type": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"workShift": "full-time"}) == EmploymentType.FULL_TIME

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Senior Engineer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Sr. Developer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Lead Architect") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Principal Engineer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Staff Engineer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Head of Engineering") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Expert Developer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Developer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Jr. Analyst") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Graduate Engineer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Entry Level") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Associate Developer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Director of Engineering") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("VP Engineering") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Vice President") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Chief Architect") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Executive Director") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Intern") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Trainee") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Software Engineer") == ExperienceLevel.MID

    async def test_search_jobs_integration(self, provider):
        mock_data = {
            "total": 1,
            "jobPostings": [
                {"id": "1", "title": "Software Engineer", "company": {"name": "Co"}, "description": "desc"},
            ],
        }
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="engineer"))
            assert len(response.results) == 1
            assert response.results[0].title == "Software Engineer"

    async def test_search_jobs_pagination(self, provider):
        mock_data = {"total": 2, "jobPostings": [{"id": "1", "title": "Dev"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)) as mock:
            await provider.search_jobs(JobSearchRequest(query="dev", offset=20))
            call_kwargs = mock.call_args[1]
            assert call_kwargs["params"]["page"] == 2

    async def test_health_check_success(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobPostings": [], "total": 0})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobPostings": [], "total": 0})):
            info = await provider.provider_info()
            assert info.name == "workday"
            assert info.is_available is True
            assert isinstance(info, JobProviderInfo)


class TestSmartRecruitersJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["smartrecruiters"])

    @pytest.fixture
    def provider(self, config):
        return SmartRecruitersJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "smartrecruiters"
        assert provider.display_name == "SmartRecruiters"
        assert provider.supports_pagination is True
        assert provider.supports_filters is True

    def test_build_search_params_query(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="developer", location="New York"))
        assert params["search"] == "developer"
        assert params["location"] == "New York"

    def test_build_search_params_remote(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="dev", remote_only=True))
        assert params["remote"] == "true"

    def test_build_search_params_keywords(self, provider):
        params = provider._build_search_params(JobSearchRequest(keywords=["java", "spring"]))
        assert params["search"] == "java spring"

    def test_parse_response(self, provider):
        data = {
            "total": 2,
            "content": [
                {"id": "sr-1", "title": "Backend Engineer", "company": {"name": "TechCo"}, "location": "NYC"},
                {"id": "sr-2", "title": "Frontend Engineer", "company": {"name": "TechCo"}, "location": "SF"},
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 2
        assert response.results[0].title == "Backend Engineer"
        assert response.results[1].company.name == "TechCo"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({"total": 0, "content": []}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_parse_response_aliases(self, provider):
        data = {"totalFound": 1, "results": [{"id": "1", "title": "Dev"}]}
        response = provider._parse_response(data, JobSearchRequest(query="dev"))
        assert len(response.results) == 1

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "sr-42",
            "title": "Senior Data Scientist",
            "company": {"name": "AICorp", "description": "ML company", "industry": "Technology"},
            "location": {"city": "Seattle", "state": "WA", "country": "US"},
            "description": "Build ML models",
            "url": "https://jobs.smartrecruiters.com/42",
            "salaryMin": 180000,
            "salaryMax": 250000,
            "salaryCurrency": "USD",
            "employmentType": "full-time",
            "skills": ["python", "tensorflow"],
            "postedDate": "2025-02-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "sr-42"
        assert posting.title == "Senior Data Scientist"
        assert posting.company.name == "AICorp"
        assert posting.company.description == "ML company"
        assert posting.company.industry == "Technology"
        assert posting.location.display_name == "Seattle, WA, US"
        assert posting.salary is not None
        assert posting.salary.min_amount == 180000
        assert posting.salary.max_amount == 250000
        assert posting.salary.currency == "USD"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["python", "tensorflow"]
        assert posting.posted_date == datetime(2025, 2, 1, tzinfo=timezone.utc)
        assert posting.provider == "smartrecruiters"

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_raw_to_posting_org_alias(self, provider):
        posting = provider._raw_to_posting({"id": "2", "title": "Dev", "organization": {"name": "OrgCo"}})
        assert posting.company.name == "OrgCo"

    def test_parse_location_dict(self, provider):
        loc = provider._parse_location({"location": {"city": "Boston", "state": "MA", "country": "US"}})
        assert loc.display_name == "Boston, MA, US"
        assert loc.remote_type == RemoteType.ON_SITE

    def test_parse_location_string(self, provider):
        loc = provider._parse_location({"location": "Remote, US"})
        assert loc.display_name == "Remote, US"

    def test_parse_location_list(self, provider):
        loc = provider._parse_location({"location": ["Chicago", "Detroit"]})
        assert "Chicago" in loc.display_name

    def test_parse_location_remote(self, provider):
        loc = provider._parse_location({"location": "Remote", "remote": True})
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salaryMin": 120000, "salaryMax": 160000})
        assert sal is not None
        assert sal.min_amount == 120000
        assert sal.max_amount == 160000

    def test_parse_salary_aliases(self, provider):
        sal = provider._parse_salary({"salaryFrom": 90000, "salaryTo": 130000})
        assert sal.min_amount == 90000
        assert sal.max_amount == 130000

    def test_parse_salary_compensation(self, provider):
        sal = provider._parse_salary({"compensation": "$70,000 - $90,000"})
        assert sal is not None
        assert sal.min_amount == 70000
        assert sal.max_amount == 90000

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"employmentType": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"employmentType": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "internship"}) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({"employmentType": "temporary"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "temp"}) == EmploymentType.TEMPORARY
        assert provider._normalize_employment({"employmentType": "freelance"}) == EmploymentType.FREELANCE
        assert provider._normalize_employment({"employmentType": "permanent"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "b2b"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "regular"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_employment_contract_type(self, provider):
        assert provider._normalize_employment({"contractType": "full-time"}) == EmploymentType.FULL_TIME

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Senior Developer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Developer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Director") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Intern") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Software Engineer") == ExperienceLevel.MID

    async def test_search_jobs_integration(self, provider):
        mock_data = {
            "total": 1,
            "content": [{"id": "1", "title": "Dev", "company": {"name": "Co"}, "description": "desc"}],
        }
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="dev"))
            assert len(response.results) == 1
            assert response.results[0].title == "Dev"

    async def test_search_jobs_pagination(self, provider):
        mock_data = {"total": 2, "content": [{"id": "1", "title": "Dev"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)) as mock:
            await provider.search_jobs(JobSearchRequest(query="dev", offset=20))
            assert mock.call_args[1]["params"]["page"] == 2

    async def test_health_check_success(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"content": [], "total": 0})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"content": [], "total": 0})):
            info = await provider.provider_info()
            assert info.name == "smartrecruiters"
            assert info.is_available is True
            assert isinstance(info, JobProviderInfo)


class TestBambooHRJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["bamboohr"])

    @pytest.fixture
    def provider(self, config):
        return BambooHRJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "bamboohr"
        assert provider.display_name == "BambooHR"
        assert provider.supports_pagination is True
        assert provider.supports_filters is True

    def test_build_search_params_query(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="engineer", location="Denver"))
        assert params["search"] == "engineer"
        assert params["location"] == "Denver"

    def test_build_search_params_keywords(self, provider):
        params = provider._build_search_params(JobSearchRequest(keywords=["react", "node"]))
        assert params["search"] == "react node"

    def test_parse_response(self, provider):
        data = {
            "total": 2,
            "jobs": [
                {"id": "bh-1", "title": "DevOps Engineer", "company": {"name": "CloudCo"}, "location": "Portland"},
                {"id": "bh-2", "title": "QA Engineer", "company": {"name": "CloudCo"}, "location": "Austin"},
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 2
        assert response.results[0].title == "DevOps Engineer"
        assert response.results[0].company.name == "CloudCo"
        assert response.metadata.total_results == 2

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({"total": 0, "jobs": []}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_parse_response_aliases(self, provider):
        data = {"totalCount": 1, "results": [{"id": "1", "title": "Dev"}]}
        response = provider._parse_response(data, JobSearchRequest(query="dev"))
        assert len(response.results) == 1

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "bh-42",
            "title": "Senior Product Manager",
            "company": {"name": "ProductCo", "description": "SaaS platform"},
            "department": {"name": "Engineering"},
            "location": {"city": "San Diego", "state": "CA", "country": "US"},
            "description": "Lead product strategy",
            "url": "https://productco.bamboohr.com/jobs/42",
            "salaryMin": 160000,
            "salaryMax": 220000,
            "salaryCurrency": "USD",
            "employmentType": "full-time",
            "skills": ["product", "analytics"],
            "postedDate": "2025-03-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "bh-42"
        assert posting.title == "Senior Product Manager"
        assert posting.company.name == "ProductCo"
        assert posting.company.description == "SaaS platform"
        assert posting.location.display_name == "San Diego, CA, US"
        assert posting.salary is not None
        assert posting.salary.min_amount == 160000
        assert posting.salary.max_amount == 220000
        assert posting.salary.currency == "USD"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["product", "analytics"]
        assert posting.posted_date == datetime(2025, 3, 1, tzinfo=timezone.utc)
        assert posting.provider == "bamboohr"

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_raw_to_posting_department_alias(self, provider):
        posting = provider._raw_to_posting({"id": "2", "title": "Dev", "department": {"name": "DeptCo"}})
        assert posting.company.name == "DeptCo"

    def test_raw_to_posting_company_name_alias(self, provider):
        posting = provider._raw_to_posting({"id": "3", "title": "Dev", "companyName": "MyCorp"})
        assert posting.company.name == "MyCorp"

    def test_raw_to_posting_company_name_underscore(self, provider):
        posting = provider._raw_to_posting({"id": "4", "title": "Dev", "company_name": "UnderscoreCo"})
        assert posting.company.name == "UnderscoreCo"

    def test_parse_location_dict(self, provider):
        loc = provider._parse_location({"location": {"city": "Miami", "state": "FL", "country": "US"}})
        assert loc.display_name == "Miami, FL, US"

    def test_parse_location_string(self, provider):
        loc = provider._parse_location({"location": "Atlanta, GA"})
        assert loc.display_name == "Atlanta, GA"

    def test_parse_location_list(self, provider):
        loc = provider._parse_location({"location": ["Phoenix", "Tucson"]})
        assert "Phoenix" in loc.display_name

    def test_parse_location_remote(self, provider):
        loc = provider._parse_location({"location": "Remote", "remote": True})
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salaryMin": 75000, "salaryMax": 110000})
        assert sal is not None
        assert sal.min_amount == 75000
        assert sal.max_amount == 110000

    def test_parse_salary_aliases(self, provider):
        sal = provider._parse_salary({"salaryMinimum": 65000, "salaryMaximum": 95000})
        assert sal.min_amount == 65000
        assert sal.max_amount == 95000

    def test_parse_salary_from_to(self, provider):
        sal = provider._parse_salary({"salaryFrom": 80000, "salaryTo": 120000})
        assert sal.min_amount == 80000
        assert sal.max_amount == 120000

    def test_parse_salary_compensation(self, provider):
        sal = provider._parse_salary({"compensation": "$90,000 - $130,000"})
        assert sal is not None
        assert sal.min_amount == 90000
        assert sal.max_amount == 130000

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"employmentType": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"employmentType": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "internship"}) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({"employmentType": "temporary"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "temp"}) == EmploymentType.TEMPORARY
        assert provider._normalize_employment({"employmentType": "freelance"}) == EmploymentType.FREELANCE
        assert provider._normalize_employment({"employmentType": "permanent"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "regular"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_employment_employment_status(self, provider):
        assert provider._normalize_employment({"employmentStatus": "full-time"}) == EmploymentType.FULL_TIME

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Senior DevOps") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Analyst") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("VP of Sales") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Intern") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Staff Engineer") == ExperienceLevel.SENIOR

    async def test_search_jobs_integration(self, provider):
        mock_data = {
            "total": 1,
            "jobs": [{"id": "1", "title": "Dev", "company": {"name": "Co"}, "description": "desc"}],
        }
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="dev"))
            assert len(response.results) == 1
            assert response.results[0].title == "Dev"

    async def test_search_jobs_pagination(self, provider):
        mock_data = {"total": 2, "jobs": [{"id": "1", "title": "Dev"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)) as mock:
            await provider.search_jobs(JobSearchRequest(query="dev", offset=20))
            assert mock.call_args[1]["params"]["page"] == 2

    async def test_health_check_success(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": [], "total": 0})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": [], "total": 0})):
            info = await provider.provider_info()
            assert info.name == "bamboohr"
            assert info.is_available is True
            assert isinstance(info, JobProviderInfo)


class TestRecruiteeJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["recruitee"])

    @pytest.fixture
    def provider(self, config):
        return RecruiteeJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "recruitee"
        assert provider.display_name == "Recruitee"
        assert provider.supports_pagination is True
        assert provider.supports_filters is True

    def test_build_search_params_query(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="designer", location="London"))
        assert params["q"] == "designer"
        assert params["location"] == "London"

    def test_build_search_params_keywords(self, provider):
        params = provider._build_search_params(JobSearchRequest(keywords=["ui", "ux"]))
        assert params["q"] == "ui ux"

    def test_build_search_params_no_query(self, provider):
        params = provider._build_search_params(JobSearchRequest())
        assert "q" not in params

    def test_parse_response(self, provider):
        data = {
            "total": 2,
            "jobs": [
                {"id": "rc-1", "title": "Full Stack Developer", "company": {"name": "DevShop"}, "location": "Berlin"},
                {"id": "rc-2", "title": "Mobile Developer", "company": {"name": "DevShop"}, "location": "Amsterdam"},
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="developer"))
        assert len(response.results) == 2
        assert response.results[0].title == "Full Stack Developer"
        assert response.results[0].company.name == "DevShop"
        assert response.metadata.total_results == 2

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({"total": 0, "jobs": []}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_parse_response_aliases(self, provider):
        data = {"offers": [{"id": "1", "title": "Dev", "companyName": "Startup"}], "total": 1}
        response = provider._parse_response(data, JobSearchRequest(query="dev"))
        assert len(response.results) == 1

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "rc-42",
            "title": "Senior Backend Engineer",
            "company": {"name": "ScaleUp", "description": "Growth company"},
            "organization": {"name": "OrgCo"},
            "location": {"city": "London", "state": "England", "country": "UK"},
            "description": "Build scalable services",
            "url": "https://scaleup.recruitee.com/jobs/42",
            "salaryMin": 90000,
            "salaryMax": 130000,
            "salaryCurrency": "GBP",
            "employmentType": "full-time",
            "skills": ["go", "k8s"],
            "postedDate": "2025-04-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "rc-42"
        assert posting.title == "Senior Backend Engineer"
        assert posting.company.name == "ScaleUp"
        assert posting.company.description == "Growth company"
        assert posting.location.display_name == "London, England, UK"
        assert posting.salary is not None
        assert posting.salary.min_amount == 90000
        assert posting.salary.max_amount == 130000
        assert posting.salary.currency == "GBP"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["go", "k8s"]
        assert posting.posted_date == datetime(2025, 4, 1, tzinfo=timezone.utc)
        assert posting.provider == "recruitee"

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_raw_to_posting_position_alias(self, provider):
        posting = provider._raw_to_posting({"id": "2", "position": "Manager", "company": {"name": "Co"}})
        assert posting.title == "Manager"

    def test_raw_to_posting_offer_id_alias(self, provider):
        posting = provider._raw_to_posting({"offerId": "rc-99", "title": "Dev", "company": {"name": "Co"}})
        assert posting.provider_job_id == "rc-99"

    def test_raw_to_posting_slug(self, provider):
        posting = provider._raw_to_posting({"slug": "backend-dev", "title": "Dev", "company": {"name": "Co"}})
        assert posting.provider_job_id == "backend-dev"

    def test_parse_location_dict(self, provider):
        loc = provider._parse_location({"location": {"city": "Paris", "country": "France"}})
        assert loc.display_name == "Paris, France"

    def test_parse_location_string(self, provider):
        loc = provider._parse_location({"location": "Toronto, ON"})
        assert loc.display_name == "Toronto, ON"

    def test_parse_location_list(self, provider):
        loc = provider._parse_location({"location": ["Dublin", "Cork"]})
        assert "Dublin" in loc.display_name

    def test_parse_location_office(self, provider):
        loc = provider._parse_location({"office": {"city": "Sydney", "country": "Australia"}})
        assert loc.display_name == "Sydney, Australia"

    def test_parse_location_remote(self, provider):
        loc = provider._parse_location({"location": "Remote", "remote": True})
        assert loc.remote_type == RemoteType.REMOTE

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salaryMin": 60000, "salaryMax": 85000})
        assert sal is not None
        assert sal.min_amount == 60000
        assert sal.max_amount == 85000

    def test_parse_salary_aliases(self, provider):
        sal = provider._parse_salary({"salaryFrom": 50000, "salaryTo": 75000})
        assert sal.min_amount == 50000
        assert sal.max_amount == 75000

    def test_parse_salary_pay_range(self, provider):
        sal = provider._parse_salary({"payRange": "$80,000 - $120,000"})
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
        assert provider._normalize_employment({"employmentType": "temporary"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "temp"}) == EmploymentType.TEMPORARY
        assert provider._normalize_employment({"employmentType": "freelance"}) == EmploymentType.FREELANCE
        assert provider._normalize_employment({"employmentType": "b2b"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "regular"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_employment_contract_type(self, provider):
        assert provider._normalize_employment({"contractType": "full-time"}) == EmploymentType.FULL_TIME

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Senior Engineer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Developer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Chief Technology Officer") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Trainee") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Software Developer") == ExperienceLevel.MID
        assert provider._normalize_experience("Lead Developer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Principal Architect") == ExperienceLevel.SENIOR

    async def test_search_jobs_integration(self, provider):
        mock_data = {
            "total": 1,
            "jobs": [{"id": "1", "title": "Dev", "company": {"name": "Co"}, "description": "desc"}],
        }
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="dev"))
            assert len(response.results) == 1
            assert response.results[0].title == "Dev"

    async def test_search_jobs_pagination(self, provider):
        mock_data = {"total": 2, "jobs": [{"id": "1", "title": "Dev"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)) as mock:
            await provider.search_jobs(JobSearchRequest(query="dev", offset=20))
            assert mock.call_args[1]["params"]["page"] == 2

    async def test_health_check_success(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": [], "total": 0})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": [], "total": 0})):
            info = await provider.provider_info()
            assert info.name == "recruitee"
            assert info.is_available is True
            assert isinstance(info, JobProviderInfo)
