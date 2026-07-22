from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.jobs.config import (
    FounditConfig,
    FreshersworldConfig,
    InternshalaConfig,
    JobDiscoveryConfig,
    NaukriConfig,
    UnstopConfig,
)
from app.jobs.exceptions import ProviderUnavailableError
from app.jobs.providers.foundit import FounditJobProvider
from app.jobs.providers.freshersworld import FreshersworldJobProvider
from app.jobs.providers.internshala import InternshalaJobProvider
from app.jobs.providers.naukri import NaukriJobProvider
from app.jobs.providers.unstop import UnstopJobProvider
from app.jobs.schemas import EmploymentType, ExperienceLevel, JobSearchRequest


def make_config(**overrides) -> JobDiscoveryConfig:
    return JobDiscoveryConfig(**overrides)


class TestConfigDefaults:
    def test_naukri_config_defaults(self):
        c = NaukriConfig()
        assert c.base_url == "https://www.naukri.com"
        assert c.page_size == 20
        assert c.rate_limit_rate == 5.0
        assert c.rate_limit_burst == 3

    def test_foundit_config_defaults(self):
        c = FounditConfig()
        assert c.base_url == "https://www.foundit.in"
        assert c.page_size == 20

    def test_internshala_config_defaults(self):
        c = InternshalaConfig()
        assert c.base_url == "https://internshala.com"
        assert c.page_size == 20

    def test_freshersworld_config_defaults(self):
        c = FreshersworldConfig()
        assert c.base_url == "https://www.freshersworld.com"
        assert c.page_size == 20

    def test_unstop_config_defaults(self):
        c = UnstopConfig()
        assert c.base_url == "https://unstop.com"
        assert c.page_size == 20


class TestNaukriJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["naukri"])

    @pytest.fixture
    def provider(self, config):
        return NaukriJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "naukri"
        assert provider.display_name == "Naukri"
        assert provider.supports_pagination is True

    def test_build_search_params_query(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="python", location="Bangalore"))
        assert params["query"] == "python"
        assert params["location"] == "Bangalore"
        assert params["limit"] == 25

    def test_build_search_params_remote(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="dev", remote_only=True))
        assert params["remote"] == "true"

    def test_build_search_params_keywords(self, provider):
        params = provider._build_search_params(JobSearchRequest(keywords=["java", "spring"]))
        assert params["query"] == "java spring"

    def test_parse_response(self, provider):
        data = {
            "total": 1,
            "jobs": [
                {
                    "id": "n-1",
                    "title": "Software Engineer",
                    "company": {"name": "Tech India"},
                    "location": "Bangalore",
                    "description": "Build software",
                },
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 1
        assert response.results[0].title == "Software Engineer"
        assert response.results[0].company.name == "Tech India"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({"total": 0, "jobs": []}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_parse_response_aliases(self, provider):
        data = {"total": 1, "results": [{"id": "2", "title": "Dev", "companyName": "Acme"}]}
        response = provider._parse_response(data, JobSearchRequest(query="dev"))
        assert len(response.results) == 1

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "n-42",
            "title": "Senior Java Developer",
            "company": {"name": "InfyCorp", "description": "IT services", "industry": "Technology", "size": "10000"},
            "location": {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
            "description": "Build enterprise apps",
            "url": "https://naukri.com/job/n-42",
            "salaryMin": 1200000,
            "salaryMax": 1800000,
            "salaryCurrency": "INR",
            "employmentType": "full-time",
            "skills": ["java", "spring"],
            "postedDate": "2024-11-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "n-42"
        assert posting.title == "Senior Java Developer"
        assert posting.company.name == "InfyCorp"
        assert posting.company.description == "IT services"
        assert posting.company.industry == "Technology"
        assert posting.company.size == "10000"
        assert posting.location.display_name == "Mumbai, Maharashtra, India"
        assert posting.salary is not None
        assert posting.salary.min_amount == 1200000
        assert posting.salary.max_amount == 1800000
        assert posting.salary.currency == "INR"
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR
        assert posting.skills == ["java", "spring"]

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_parse_location_dict(self, provider):
        loc = provider._parse_location({"location": {"city": "Delhi", "state": "Delhi", "country": "India"}})
        assert loc.display_name == "Delhi, Delhi, India"

    def test_parse_location_string(self, provider):
        loc = provider._parse_location({"location": "Pune, India"})
        assert loc.display_name == "Pune, India"

    def test_parse_location_list(self, provider):
        loc = provider._parse_location({"location": ["Bangalore", "Hyderabad"]})
        assert "Bangalore" in loc.display_name

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salaryMin": 500000, "salaryMax": 1000000})
        assert sal is not None
        assert sal.min_amount == 500000
        assert sal.max_amount == 1000000
        assert sal.currency == "INR"

    def test_parse_salary_string(self, provider):
        sal = provider._parse_salary({"salary": "\u20b95,00,000 - \u20b910,00,000"})
        assert sal is not None
        assert sal.currency == "INR"

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"employmentType": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"employmentType": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({"employmentType": "internship"}) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({"employmentType": "temp"}) == EmploymentType.TEMPORARY
        assert provider._normalize_employment({"employmentType": "freelance"}) == EmploymentType.FREELANCE
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Principal Architect") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Developer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("VP Engineering") == ExperienceLevel.EXECUTIVE
        assert provider._normalize_experience("Fresher Trainee") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Software Engineer") == ExperienceLevel.MID

    async def test_search_jobs_integration(self, provider):
        mock_data = {"total": 1, "jobs": [{"id": "1", "title": "Dev"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="dev"))
            assert len(response.results) == 1

    async def test_health_check(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"total": 0, "jobs": []})):
            assert await provider.health_check() is True

    async def test_health_check_failure(self, provider):
        with patch.object(provider._client, "get", AsyncMock(side_effect=ProviderUnavailableError("fail"))):
            assert await provider.health_check() is False

    async def test_provider_info(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"total": 0, "jobs": []})):
            info = await provider.provider_info()
            assert info.name == "naukri"
            assert info.is_available is True


class TestFounditJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["foundit"])

    @pytest.fixture
    def provider(self, config):
        return FounditJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "foundit"
        assert provider.display_name == "Foundit"

    def test_build_search_params(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="developer", location="Chennai"))
        assert params["query"] == "developer"
        assert params["location"] == "Chennai"

    def test_parse_response(self, provider):
        data = {"total": 1, "jobs": [{"id": "f-1", "title": "Full Stack Dev", "company": {"name": "FounditCo"}}]}
        response = provider._parse_response(data, JobSearchRequest(query="dev"))
        assert len(response.results) == 1
        assert response.results[0].company.name == "FounditCo"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "f-42",
            "title": "Senior Data Analyst",
            "company": {"name": "AnalyticsPro", "industry": "Analytics"},
            "location": {"city": "Hyderabad", "state": "Telangana"},
            "description": "Analyze data",
            "url": "https://foundit.in/job/f-42",
            "salaryMin": 800000,
            "salaryMax": 1500000,
            "skills": ["python", "sql"],
            "employmentType": "full-time",
            "postedDate": "2024-12-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "f-42"
        assert posting.title == "Senior Data Analyst"
        assert posting.company.name == "AnalyticsPro"
        assert posting.salary is not None
        assert posting.salary.min_amount == 800000
        assert posting.salary.max_amount == 1500000
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None
        assert posting.employment_type == EmploymentType.OTHER
        assert posting.experience_level == ExperienceLevel.MID

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salaryMin": 300000, "salaryMax": 600000})
        assert sal.currency == "INR"

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"employmentType": "permanent"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"employmentType": "contract"}) == EmploymentType.CONTRACT
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Lead Engineer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Entry Level Analyst") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Fresher") == ExperienceLevel.ENTRY

    async def test_search_jobs_integration(self, provider):
        mock_data = {"total": 1, "jobs": [{"id": "1", "title": "Dev"}]}
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
            assert info.name == "foundit"
            assert info.is_available is True


class TestInternshalaJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["internshala"])

    @pytest.fixture
    def provider(self, config):
        return InternshalaJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "internshala"
        assert provider.display_name == "Internshala"

    def test_build_search_params(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="marketing", location="Mumbai"))
        assert params["query"] == "marketing"
        assert params["location"] == "Mumbai"

    def test_parse_response(self, provider):
        data = {
            "total": 1,
            "internships": [
                {
                    "id": "is-1",
                    "title": "Content Writer Intern",
                    "company": {"name": "MediaCo"},
                    "type": "internship",
                },
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="intern"))
        assert len(response.results) == 1
        assert response.results[0].company.name == "MediaCo"

    def test_parse_response_aliases(self, provider):
        data = {"total": 1, "jobs": [{"id": "2", "title": "Dev Intern", "companyName": "Co"}]}
        response = provider._parse_response(data, JobSearchRequest(query="intern"))
        assert len(response.results) == 1

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_raw_to_posting_internship(self, provider):
        raw = {
            "id": "is-42",
            "title": "Software Development Intern",
            "company": {"name": "StartupIndia"},
            "location": {"city": "Bangalore", "state": "Karnataka"},
            "description": "Build features",
            "url": "https://internshala.com/internship/is-42",
            "stipend": "\u20b910,000 - \u20b920,000",
            "skills": ["python"],
            "type": "internship",
            "postedDate": "2024-10-15T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "is-42"
        assert posting.title == "Software Development Intern"
        assert posting.employment_type == EmploymentType.INTERNSHIP
        assert posting.experience_level == ExperienceLevel.ENTRY
        assert posting.salary is not None
        assert posting.salary.currency == "INR"
        assert posting.salary.period == "monthly"

    def test_raw_to_posting_full_time(self, provider):
        raw = {
            "id": "is-99",
            "title": "Senior Marketing Manager",
            "company": {"name": "BrandCo"},
            "description": "Lead marketing",
            "employmentType": "full-time",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Intern"})
        assert posting.employment_type == EmploymentType.INTERNSHIP
        assert posting.experience_level == ExperienceLevel.ENTRY

    def test_parse_salary_stipend(self, provider):
        sal = provider._parse_salary({"stipendMin": 5000, "stipendMax": 15000})
        assert sal is not None
        assert sal.min_amount == 5000
        assert sal.max_amount == 15000
        assert sal.period == "monthly"

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"type": "full-time"}) == EmploymentType.FULL_TIME
        assert provider._normalize_employment({"type": "internship"}) == EmploymentType.INTERNSHIP
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Staff Engineer") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Designer") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Fresher Program") == ExperienceLevel.ENTRY

    async def test_search_jobs_integration(self, provider):
        mock_data = {"total": 1, "internships": [{"id": "1", "title": "Intern"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="intern"))
            assert len(response.results) == 1

    async def test_health_check(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"internships": []})):
            assert await provider.health_check() is True


class TestFreshersworldJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["freshersworld"])

    @pytest.fixture
    def provider(self, config):
        return FreshersworldJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "freshersworld"
        assert provider.display_name == "Freshersworld"

    def test_build_search_params(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="engineer", location="Pune"))
        assert params["query"] == "engineer"
        assert params["location"] == "Pune"

    def test_parse_response(self, provider):
        data = {"total": 1, "jobs": [{"id": "fw-1", "title": "Graduate Engineer", "companyName": "TechCorp"}]}
        response = provider._parse_response(data, JobSearchRequest(query="engineer"))
        assert len(response.results) == 1
        assert response.results[0].company.name == "TechCorp"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "fw-42",
            "title": "Fresher Software Developer",
            "company": {"name": "CodeBase", "industry": "Software"},
            "location": {"city": "Chennai", "state": "Tamil Nadu"},
            "description": "Entry level dev role",
            "url": "https://freshersworld.com/job/fw-42",
            "salaryMin": 300000,
            "salaryMax": 500000,
            "skills": ["c++", "python"],
            "employmentType": "full-time",
            "postedDate": "2024-09-01T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "fw-42"
        assert posting.title == "Fresher Software Developer"
        assert posting.company.name == "CodeBase"
        assert posting.salary.min_amount == 300000
        assert posting.salary.max_amount == 500000
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.ENTRY

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salaryMin": 200000})
        assert sal.min_amount == 200000
        assert sal.currency == "INR"

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Fresher Engineer") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Trainee Developer") == ExperienceLevel.ENTRY
        assert provider._normalize_experience("Software Developer") == ExperienceLevel.MID

    async def test_search_jobs_integration(self, provider):
        mock_data = {"total": 1, "jobs": [{"id": "1", "title": "Fresher Dev"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="fresher"))
            assert len(response.results) == 1

    async def test_health_check(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"jobs": []})):
            assert await provider.health_check() is True


class TestUnstopJobProvider:
    @pytest.fixture
    def config(self):
        return make_config(enabled_providers=["unstop"])

    @pytest.fixture
    def provider(self, config):
        return UnstopJobProvider(config)

    def test_provider_attributes(self, provider):
        assert provider.name == "unstop"
        assert provider.display_name == "Unstop"

    def test_build_search_params(self, provider):
        params = provider._build_search_params(JobSearchRequest(query="design", location="Delhi"))
        assert params["query"] == "design"
        assert params["location"] == "Delhi"

    def test_parse_response(self, provider):
        data = {
            "total": 1,
            "data": [
                {
                    "id": "u-1",
                    "title": "Design Challenge",
                    "organization": {"name": "DesignOrg"},
                },
            ],
        }
        response = provider._parse_response(data, JobSearchRequest(query="design"))
        assert len(response.results) == 1
        assert response.results[0].company.name == "DesignOrg"

    def test_parse_response_aliases(self, provider):
        data = {"total": 1, "opportunities": [{"id": "2", "title": "Hackathon", "orgName": "TechOrg"}]}
        response = provider._parse_response(data, JobSearchRequest(query="hack"))
        assert len(response.results) == 1
        assert response.results[0].company.name == "TechOrg"

    def test_parse_response_empty(self, provider):
        response = provider._parse_response({}, JobSearchRequest(query="x"))
        assert len(response.results) == 0

    def test_raw_to_posting_full(self, provider):
        raw = {
            "id": "u-42",
            "title": "Senior Product Designer",
            "organization": {"name": "DesignStudio", "description": "Creative agency", "website": "https://ds.com"},
            "location": {"city": "Bangalore", "state": "Karnataka"},
            "description": "Lead design team",
            "url": "https://unstop.com/opportunity/u-42",
            "salaryMin": 1500000,
            "salaryMax": 2500000,
            "skills": ["figma", "ui"],
            "employmentType": "full-time",
            "postedDate": "2024-08-15T00:00:00Z",
        }
        posting = provider._raw_to_posting(raw)
        assert posting.provider_job_id == "u-42"
        assert posting.title == "Senior Product Designer"
        assert posting.company.name == "DesignStudio"
        assert posting.company.website == "https://ds.com"
        assert posting.salary is not None
        assert posting.salary.min_amount == 1500000
        assert posting.salary.max_amount == 2500000
        assert posting.employment_type == EmploymentType.FULL_TIME
        assert posting.experience_level == ExperienceLevel.SENIOR

    def test_raw_to_posting_internship(self, provider):
        raw = {"id": "u-99", "title": "Marketing Intern", "type": "internship"}
        posting = provider._raw_to_posting(raw)
        assert posting.employment_type == EmploymentType.INTERNSHIP
        assert posting.experience_level == ExperienceLevel.ENTRY

    def test_raw_to_posting_minimal(self, provider):
        posting = provider._raw_to_posting({"id": "1", "title": "Dev"})
        assert posting.company.name == "Unknown Company"
        assert posting.salary is None

    def test_parse_salary(self, provider):
        sal = provider._parse_salary({"salaryMin": 600000, "salaryMax": 1200000})
        assert sal.min_amount == 600000
        assert sal.currency == "INR"

    def test_parse_salary_prize(self, provider):
        sal = provider._parse_salary({"prizeMin": 50000, "prizeMax": 100000})
        assert sal is not None

    def test_parse_salary_none(self, provider):
        assert provider._parse_salary({}) is None

    def test_normalize_employment(self, provider):
        assert provider._normalize_employment({"type": "part-time"}) == EmploymentType.PART_TIME
        assert provider._normalize_employment({"type": "freelance"}) == EmploymentType.FREELANCE
        assert provider._normalize_employment({}) == EmploymentType.OTHER

    def test_normalize_experience(self, provider):
        assert provider._normalize_experience("Head of Design") == ExperienceLevel.SENIOR
        assert provider._normalize_experience("Junior Analyst") == ExperienceLevel.JUNIOR
        assert provider._normalize_experience("Fresher Opportunity") == ExperienceLevel.ENTRY

    async def test_search_jobs_integration(self, provider):
        mock_data = {"total": 1, "data": [{"id": "1", "title": "Opportunity"}]}
        with patch.object(provider._client, "get", AsyncMock(return_value=mock_data)):
            response = await provider.search_jobs(JobSearchRequest(query="opp"))
            assert len(response.results) == 1

    async def test_health_check(self, provider):
        with patch.object(provider._client, "get", AsyncMock(return_value={"data": []})):
            assert await provider.health_check() is True


class TestIndiaFactoryRegistrations:
    def test_register_naukri(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["naukri"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "naukri" in names

    def test_register_foundit(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["foundit"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "foundit" in names

    def test_register_internshala(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["internshala"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "internshala" in names

    def test_register_freshersworld(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["freshersworld"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "freshersworld" in names

    def test_register_unstop(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["unstop"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "unstop" in names

    def test_register_all_india(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=["naukri", "foundit", "internshala", "freshersworld", "unstop"])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        for n in ("naukri", "foundit", "internshala", "freshersworld", "unstop"):
            assert n in names

    def test_skip_when_not_enabled(self):
        from app.jobs.factory import JobProviderFactory

        registry = MagicMock()
        registry.is_registered.return_value = False
        config = make_config(enabled_providers=[])
        factory = JobProviderFactory(registry, config)
        factory.register_all()
        names = [call[0][0].name for call in registry.register.call_args_list]
        assert "naukri" not in names
        assert "internshala" not in names


class TestIndiaProviderConfig:
    def test_job_discovery_config_with_all(self):
        config = make_config(
            enabled_providers=["naukri", "foundit", "internshala", "freshersworld", "unstop"],
            naukri=NaukriConfig(base_url="https://custom.naukri.com"),
            internshala=InternshalaConfig(page_size=30),
        )
        assert config.naukri.base_url == "https://custom.naukri.com"
        assert config.internshala.page_size == 30

    def test_page_size_validation(self):
        with pytest.raises(Exception):
            NaukriConfig(page_size=0)
        with pytest.raises(Exception):
            FounditConfig(page_size=100)
        with pytest.raises(Exception):
            InternshalaConfig(page_size=-1)
        with pytest.raises(Exception):
            FreshersworldConfig(page_size=0)
        with pytest.raises(Exception):
            UnstopConfig(page_size=101)
