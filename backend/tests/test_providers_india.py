"""Unit tests for the India & Y Combinator provider implementations."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.services.job_normalizer import JobNormalizer
from app.services.providers.base import RawJobData
from app.services.providers.config import PROVIDER_CONFIGS
from app.services.providers.factory import ProviderFactory
from app.services.providers.implementations.foundit import FounditProvider
from app.services.providers.implementations.freshersworld import FreshersworldProvider
from app.services.providers.implementations.internshala import InternshalaProvider
from app.services.providers.implementations.naukri import NaukriProvider
from app.services.providers.implementations.unstop import UnstopProvider
from app.services.providers.implementations.ycombinator import YCombinatorProvider

# ── Config Tests ──


class TestNewProviderConfigs:
    def test_all_new_providers_have_configs(self):
        expected = [
            "ycombinator", "naukri", "foundit",
            "internshala", "unstop", "freshersworld",
        ]
        for name in expected:
            assert name in PROVIDER_CONFIGS, f"Missing config for {name}"

    def test_all_new_configs_have_base_url(self):
        for name in ("ycombinator", "naukri", "foundit", "internshala", "unstop", "freshersworld"):
            config = PROVIDER_CONFIGS[name]
            assert config.base_url != "", f"Empty base_url for {name}"
            assert config.enabled is True

    def test_all_new_configs_have_reasonable_rate_limits(self):
        for name in ("ycombinator", "naukri", "foundit", "internshala", "unstop", "freshersworld"):
            config = PROVIDER_CONFIGS[name]
            assert config.requests_per_second > 0
            assert config.max_retries >= 2
            assert config.timeout_seconds >= 15


# ── Y Combinator ──


class TestYCombinatorProvider:
    @pytest.mark.asyncio
    async def test_name(self):
        provider = YCombinatorProvider()
        assert provider.name == "ycombinator"

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_failure(self):
        provider = YCombinatorProvider()
        with patch.object(provider, "_get_json", AsyncMock(side_effect=Exception("API down"))):
            results = await provider.search("Python Developer")
            assert results == []

    @pytest.mark.asyncio
    async def test_parse_jobs_with_data(self):
        provider = YCombinatorProvider()
        data = {
            "jobs": [
                {
                    "id": 1,
                    "title": "Software Engineer",
                    "company_name": "StartupCo",
                    "job_description": "Build amazing things",
                    "location": "San Francisco, CA",
                    "url": "https://startupco.com/jobs/1",
                    "salary_min": 120000,
                    "salary_max": 180000,
                    "salary_currency": "USD",
                    "salary_period": "yearly",
                    "job_type": "full-time",
                    "remote": True,
                    "created_at": "2026-07-15T00:00:00Z",
                    "skills": ["Python", "React"],
                },
                {
                    "id": 2,
                    "title": "Frontend Developer",
                    "company_name": "WebCo",
                    "job_description": "Build UIs",
                    "location": "Remote",
                    "url": "https://webco.com/jobs/2",
                    "remote": True,
                    "skills": ["JavaScript"],
                },
            ]
        }
        results = provider._parse_jobs(data, "Engineer")
        assert len(results) == 2
        assert results[0].title == "Software Engineer"
        assert results[0].company_name == "StartupCo"
        assert results[0].salary_min == 120000.0
        assert results[0].salary_max == 180000.0
        assert results[0].salary_currency == "USD"
        assert results[0].remote is True
        assert results[0].skills == ["Python", "React"]
        assert results[1].company_name == "WebCo"

    @pytest.mark.asyncio
    async def test_factory_creates_provider(self):
        factory = ProviderFactory()
        factory.register_class("ycombinator", YCombinatorProvider)
        provider = factory.create("ycombinator")
        assert provider.name == "ycombinator"
        assert provider.enabled is True


# ── Naukri ──


class TestNaukriProvider:
    @pytest.mark.asyncio
    async def test_name(self):
        provider = NaukriProvider()
        assert provider.name == "naukri"

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_failure(self):
        provider = NaukriProvider()
        with patch.object(provider, "_get_html", AsyncMock(side_effect=Exception("Down"))):
            results = await provider.search("Python Developer")
            assert results == []

    @pytest.mark.asyncio
    async def test_parse_salary_inr_lakh(self):
        provider = NaukriProvider()
        result = provider._parse_salary("₹6 - 12 Lacs p.a.")
        assert result[0] == 600000.0
        assert result[1] == 1200000.0
        assert result[2] == "INR"
        assert result[3] == "yearly"

    @pytest.mark.asyncio
    async def test_parse_salary_inr_single(self):
        provider = NaukriProvider()
        result = provider._parse_salary("₹5 Lacs")
        assert result[0] == 500000.0
        assert result[2] == "INR"

    @pytest.mark.asyncio
    async def test_parse_date(self):
        provider = NaukriProvider()
        assert provider._parse_date("Just now") is not None
        assert provider._parse_date("Today") is not None
        assert provider._parse_date("3 days ago") is not None
        assert provider._parse_date("") is None
        assert provider._parse_date(None) is None

    @pytest.mark.asyncio
    async def test_extract_job_id(self):
        from bs4 import BeautifulSoup
        provider = NaukriProvider()
        html = '<div data-job-id="12345"></div>'
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert provider._extract_job_id(card) == "12345"

    @pytest.mark.asyncio
    async def test_factory_creates_provider(self):
        factory = ProviderFactory()
        factory.register_class("naukri", NaukriProvider)
        provider = factory.create("naukri")
        assert provider.name == "naukri"


# ── Foundit ──


class TestFounditProvider:
    @pytest.mark.asyncio
    async def test_name(self):
        provider = FounditProvider()
        assert provider.name == "foundit"

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_failure(self):
        provider = FounditProvider()
        with patch.object(provider, "_get_html", AsyncMock(side_effect=Exception("Down"))):
            results = await provider.search("Python Developer")
            assert results == []

    @pytest.mark.asyncio
    async def test_parse_salary_inr(self):
        provider = FounditProvider()
        result = provider._parse_salary("₹3 - 6 Lakhs")
        assert result[0] == 300000.0
        assert result[1] == 600000.0
        assert result[2] == "INR"

    @pytest.mark.asyncio
    async def test_parse_salary_no_match(self):
        provider = FounditProvider()
        result = provider._parse_salary("Not disclosed")
        assert result[0] is None
        assert result[1] is None

    @pytest.mark.asyncio
    async def test_parse_date(self):
        provider = FounditProvider()
        assert provider._parse_date("Posted 2 days ago") is not None
        assert provider._parse_date("Today") is not None
        assert provider._parse_date(None) is None

    @pytest.mark.asyncio
    async def test_factory_creates_provider(self):
        factory = ProviderFactory()
        factory.register_class("foundit", FounditProvider)
        provider = factory.create("foundit")
        assert provider.name == "foundit"


# ── Internshala ──


class TestInternshalaProvider:
    @pytest.mark.asyncio
    async def test_name(self):
        provider = InternshalaProvider()
        assert provider.name == "internshala"

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_failure(self):
        provider = InternshalaProvider()
        with patch.object(provider, "_get_html", AsyncMock(side_effect=Exception("Down"))):
            results = await provider.search("Python Developer")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_passes_category(self):
        provider = InternshalaProvider()
        with (
            patch.object(provider, "_get_html", AsyncMock(return_value="<html></html>")),
            patch.object(provider, "_parse_search_results", return_value=[]),
        ):
            await provider.search("Python", category="jobs")
            url_called = provider._get_html.call_args[0][0]
            assert "jobs" in url_called or "internships" in url_called

    @pytest.mark.asyncio
    async def test_parse_stipend_monthly(self):
        provider = InternshalaProvider()
        result = provider._parse_stipend("₹10,000 - ₹15,000 /month")
        assert result[0] == 10000.0
        assert result[1] == 15000.0
        assert result[2] == "INR"
        assert result[3] == "monthly"

    @pytest.mark.asyncio
    async def test_parse_stipend_single(self):
        provider = InternshalaProvider()
        result = provider._parse_stipend("₹5,000")
        assert result[0] == 5000.0
        assert result[2] == "INR"
        assert result[3] == "monthly"

    @pytest.mark.asyncio
    async def test_parse_date(self):
        provider = InternshalaProvider()
        assert provider._parse_date("Just now") is not None
        assert provider._parse_date("1 day ago") is not None
        assert provider._parse_date(None) is None

    @pytest.mark.asyncio
    async     def test_extract_job_id(self):
        from bs4 import BeautifulSoup
        provider = InternshalaProvider()
        html = '<div class="card"><a href="/internship/python-internship-1234"></a></div>'
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert provider._extract_job_id(card) == "1234"

    @pytest.mark.asyncio
    async def test_factory_creates_provider(self):
        factory = ProviderFactory()
        factory.register_class("internshala", InternshalaProvider)
        provider = factory.create("internshala")
        assert provider.name == "internshala"


# ── Unstop ──


class TestUnstopProvider:
    @pytest.mark.asyncio
    async def test_name(self):
        provider = UnstopProvider()
        assert provider.name == "unstop"

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_failure(self):
        provider = UnstopProvider()
        with patch.object(provider, "_get_html", AsyncMock(side_effect=Exception("Down"))):
            results = await provider.search("Python Developer")
            assert results == []

    @pytest.mark.asyncio
    async def test_parse_stipend(self):
        provider = UnstopProvider()
        result = provider._parse_stipend("₹20,000 - ₹30,000")
        assert result[0] == 20000.0
        assert result[1] == 30000.0
        assert result[2] == "INR"
        assert result[3] == "monthly"

    @pytest.mark.asyncio
    async def test_parse_stipend_lakh(self):
        provider = UnstopProvider()
        result = provider._parse_stipend("₹3 Lakhs")
        assert result[0] == 300000.0
        assert result[2] == "INR"
        assert result[3] == "yearly"

    @pytest.mark.asyncio
    async def test_parse_stipend_k_format(self):
        provider = UnstopProvider()
        result = provider._parse_stipend("₹50k")
        assert result[0] == 50000.0
        assert result[2] == "INR"

    @pytest.mark.asyncio
    async def test_parse_date(self):
        provider = UnstopProvider()
        assert provider._parse_date("Posted 1 week ago") is not None
        assert provider._parse_date("Today") is not None
        assert provider._parse_date(None) is None

    @pytest.mark.asyncio
    async     def test_extract_opportunity_id(self):
        from bs4 import BeautifulSoup
        provider = UnstopProvider()
        html = '<div class="card"><a href="/opportunity/abc123"></a></div>'
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert provider._extract_opportunity_id(card) == "abc123"

    @pytest.mark.asyncio
    async def test_factory_creates_provider(self):
        factory = ProviderFactory()
        factory.register_class("unstop", UnstopProvider)
        provider = factory.create("unstop")
        assert provider.name == "unstop"


# ── Freshersworld ──


class TestFreshersworldProvider:
    @pytest.mark.asyncio
    async def test_name(self):
        provider = FreshersworldProvider()
        assert provider.name == "freshersworld"

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_failure(self):
        provider = FreshersworldProvider()
        with patch.object(provider, "_get_html", AsyncMock(side_effect=Exception("Down"))):
            results = await provider.search("Python Developer")
            assert results == []

    @pytest.mark.asyncio
    async def test_parse_salary_inr(self):
        provider = FreshersworldProvider()
        result = provider._parse_salary("₹2 - 4 Lakhs per year")
        assert result[0] == 200000.0
        assert result[1] == 400000.0
        assert result[2] == "INR"
        assert result[3] == "yearly"

    @pytest.mark.asyncio
    async def test_parse_salary_no_numbers(self):
        provider = FreshersworldProvider()
        result = provider._parse_salary("Not mentioned")
        assert result[0] is None
        assert result[1] is None

    @pytest.mark.asyncio
    async def test_parse_date(self):
        provider = FreshersworldProvider()
        assert provider._parse_date("Just now") is not None
        assert provider._parse_date("5 days ago") is not None
        assert provider._parse_date(None) is None

    @pytest.mark.asyncio
    async def test_factory_creates_provider(self):
        factory = ProviderFactory()
        factory.register_class("freshersworld", FreshersworldProvider)
        provider = factory.create("freshersworld")
        assert provider.name == "freshersworld"


# ── Registration Tests ──


class TestProviderRegistration:
    def test_all_new_providers_register_in_factory(self):
        factory = ProviderFactory()
        providers = [
            ("ycombinator", YCombinatorProvider),
            ("naukri", NaukriProvider),
            ("foundit", FounditProvider),
            ("internshala", InternshalaProvider),
            ("unstop", UnstopProvider),
            ("freshersworld", FreshersworldProvider),
        ]
        for name, cls in providers:
            factory.register_class(name, cls)

        created = factory.create_all()
        assert "ycombinator" in created
        assert "naukri" in created
        assert "foundit" in created
        assert "internshala" in created
        assert "unstop" in created
        assert "freshersworld" in created
        assert len(created) == 6

    def test_search_all_skips_failed_providers(self):
        factory = ProviderFactory()
        factory.register_class("ycombinator", YCombinatorProvider)
        factory.register_class("naukri", NaukriProvider)
        result = factory.create_all(["ycombinator", "naukri", "nonexistent_provider"])
        assert "ycombinator" in result
        assert "naukri" in result
        assert "nonexistent_provider" not in result


# ── Normalization Tests ──


class TestNewProviderNormalization:
    def test_ycombinator_normalization(self):
        normalizer = JobNormalizer()
        raw = RawJobData(
            title="Software Engineer",
            company_name="StartupCo",
            description="Build amazing things",
            location="San Francisco, CA",
            url="https://startupco.com/jobs/1",
            source_job_id="42",
            salary_min=120000.0,
            salary_max=180000.0,
            salary_currency="USD",
            salary_period="yearly",
            remote=True,
            skills=["Python", "React"],
            raw={"source": "ycombinator", "query": "engineer"},
        )
        job = normalizer.normalize(raw)
        assert job.title == "Software Engineer"
        assert job.company_name == "StartupCo"
        assert job.source == "ycombinator"
        assert job.salary_min == 120000.0
        assert job.remote is True
        assert "Python" in job.skills
        assert job.content_hash is not None

    def test_naukri_normalization(self):
        normalizer = JobNormalizer()
        raw = RawJobData(
            title="Python Developer",
            company_name="TechCorp",
            location="Bangalore",
            url="https://www.naukri.com/job/123",
            salary_min=600000.0,
            salary_max=1200000.0,
            salary_currency="INR",
            salary_period="yearly",
            skills=["Python", "Django"],
            raw={"source": "naukri", "query": "python"},
        )
        job = normalizer.normalize(raw)
        assert job.title == "Python Developer"
        assert job.company_name == "TechCorp"
        assert job.source == "naukri"
        assert job.salary_currency == "INR"
        assert job.content_hash is not None

    def test_foundit_normalization(self):
        normalizer = JobNormalizer()
        raw = RawJobData(
            title="Data Analyst",
            company_name="AnalyticsCo",
            location="Mumbai",
            raw={"source": "foundit", "query": "analyst"},
        )
        job = normalizer.normalize(raw)
        assert job.title == "Data Analyst"
        assert job.source == "foundit"
        assert job.content_hash is not None

    def test_internshala_normalization(self):
        normalizer = JobNormalizer()
        raw = RawJobData(
            title="Web Development Intern",
            company_name="StartupInc",
            location="Delhi",
            job_type="internship",
            salary_min=10000.0,
            salary_period="monthly",
            salary_currency="INR",
            skills=["HTML", "CSS"],
            raw={"source": "internshala", "query": "web", "category": "internships"},
        )
        job = normalizer.normalize(raw)
        assert job.title == "Web Development Intern"
        assert job.source == "internshala"
        assert job.job_type == "internship"
        assert job.salary_min == 10000.0
        assert "HTML" in job.skills

    def test_unstop_normalization(self):
        normalizer = JobNormalizer()
        raw = RawJobData(
            title="Hackathon Participant",
            company_name="Unstop Corp",
            location="Remote",
            remote=True,
            job_type="competition",
            raw={"source": "unstop", "query": "hackathon", "opportunity_type": "competitions"},
        )
        job = normalizer.normalize(raw)
        assert job.title == "Hackathon Participant"
        assert job.source == "unstop"
        assert job.remote is True

    def test_freshersworld_normalization(self):
        normalizer = JobNormalizer()
        raw = RawJobData(
            title="Graduate Engineer Trainee",
            company_name="MegaCorp",
            location="Chennai",
            job_type="entry-level",
            raw={"source": "freshersworld", "query": "engineer", "experience": "0-1 years"},
        )
        job = normalizer.normalize(raw)
        assert job.title == "Graduate Engineer Trainee"
        assert job.source == "freshersworld"
        assert job.job_type == "entry-level"


# ── Support Tests ──


class TestNewProviderSupport:
    def test_ycombinator_supports_keyword_search(self):
        provider = YCombinatorProvider()
        with patch.object(provider, "_get_json", AsyncMock(return_value={"jobs": []})):
            results = asyncio.run(provider.search("Python Developer"))
            assert results == []

    def test_naukri_supports_location_filter(self):
        provider = NaukriProvider()
        with (
            patch.object(provider, "_get_html", AsyncMock(return_value="<html></html>")),
            patch.object(provider, "_parse_search_results", return_value=[]),
        ):
            asyncio.run(provider.search("Python", location="Bangalore"))
            called_params = provider._get_html.call_args[1].get("params", {})
            assert called_params.get("l") == "Bangalore"

    def test_foundit_supports_location_filter(self):
        provider = FounditProvider()
        with (
            patch.object(provider, "_get_html", AsyncMock(return_value="<html></html>")),
            patch.object(provider, "_parse_search_results", return_value=[]),
        ):
            asyncio.run(provider.search("Python", location="Mumbai"))
            called_params = provider._get_html.call_args[1].get("params", {})
            assert called_params.get("city") == "Mumbai"
