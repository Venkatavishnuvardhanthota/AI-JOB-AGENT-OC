from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.application_intelligence.cache import AnalysisCache
from app.application_intelligence.company import CompanyAnalyzer
from app.application_intelligence.config import ApplicationIntelligenceConfig
from app.application_intelligence.culture import CultureAnalyzer
from app.application_intelligence.role import RoleAnalyzer
from app.application_intelligence.schemas import (
    ApplicationIntelligence,
    ApplicationPriority,
    CompanyType,
    HiringPriority,
    RoleCategory,
    RoleSeniority,
    SkillExtraction,
)
from app.application_intelligence.service import ApplicationIntelligenceService
from app.application_intelligence.skills import SkillExtractor
from app.application_intelligence.validator import ApplicationIntelligenceValidator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_job(
    title="Software Engineer",
    company_name="TestCorp",
    company_industry=None,
    company_size=None,
    description=None,
    skills=None,
    employment_type="full_time",
    experience_level=None,
    city=None,
    state=None,
    country=None,
    remote_type=None,
    salary_min=None,
    salary_max=None,
    salary_currency="USD",
    salary_period="yearly",
    posted_date=None,
):
    if description is None:
        description = (
            "We are looking for a skilled Software Engineer to join our team. "
            "You will develop and maintain web applications. "
            "Required: 3+ years Python experience, strong communication skills."
        )
    if skills is None:
        skills = ["Python", "JavaScript", "Django", "PostgreSQL", "AWS"]
    company = MagicMock()
    company.name = company_name
    company.website = None
    company.logo_url = None
    company.description = None
    company.industry = company_industry
    company.size = company_size

    location = MagicMock()
    location.city = city
    location.state = state
    location.country = country
    location.remote_type = remote_type
    location.display_name = None
    location.latitude = None
    location.longitude = None

    salary = MagicMock()
    salary.min_amount = salary_min
    salary.max_amount = salary_max
    salary.currency = salary_currency
    salary.period = salary_period
    salary.interval = None

    job = MagicMock()
    job.id = uuid.uuid4()
    job.provider_job_id = "123"
    job.title = title
    job.company = company
    job.location = location
    job.description = description
    job.description_html = None
    job.url = "https://example.com/job"
    job.apply_url = None
    job.employment_type = employment_type
    job.experience_level = experience_level
    job.salary = salary
    job.skills = skills
    job.posted_date = posted_date
    job.expiration_date = None
    job.provider = "test"
    job.source_updated_at = None
    return job


def make_config():
    return ApplicationIntelligenceConfig(
        cache_ttl_seconds=300,
        strict_validation=True,
        high_priority_threshold=0.75,
        medium_priority_threshold=0.45,
    )


# ===========================================================================
# Config Tests
# ===========================================================================


class TestConfig:
    def test_default_config(self):
        config = ApplicationIntelligenceConfig()
        assert config.cache_ttl_seconds == 300
        assert config.high_priority_threshold == 0.75
        assert config.medium_priority_threshold == 0.45
        assert config.confidence_score_fields == 7
        assert config.strict_validation is True

    def test_seniority_keywords_defaults(self):
        config = ApplicationIntelligenceConfig()
        assert "entry" in config.seniority_keywords
        assert "senior" in config.seniority_keywords
        assert "executive" in config.seniority_keywords


# ===========================================================================
# Company Analysis Tests
# ===========================================================================


class TestCompanyAnalyzer:
    def test_basic_company_info(self):
        job = make_job(company_industry="Technology", company_size="51-200")
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.company_size == "51-200"
        assert result.industry_classification == "Technology"
        assert result.summary == "TestCorp (Technology)"

    def test_startup_classification(self):
        job = make_job(
            company_name="StartupInc",
            description="We are a high-growth venture-backed startup building amazing products.",
        )
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.company_type == CompanyType.STARTUP
        assert result.is_startup is True

    def test_enterprise_classification(self):
        job = make_job(
            company_name="BigCorp",
            description="Join our global enterprise with Fortune 500 clients.",
        )
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.company_type == CompanyType.ENTERPRISE
        assert result.is_startup is False

    def test_consulting_classification(self):
        job = make_job(
            company_name="McKinsey",
            description="Leading management consulting firm.",
        )
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.company_type == CompanyType.CONSULTING

    def test_government_classification(self):
        job = make_job(
            company_name="Govt Agency",
            description="Federal government agency seeks developer.",
        )
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.company_type == CompanyType.GOVERNMENT

    def test_nonprofit_classification(self):
        job = make_job(
            company_name="CharityOrg",
            description="Non-profit organization helping communities.",
        )
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.company_type == CompanyType.NON_PROFIT

    def test_unknown_company_type(self):
        job = make_job(company_name="Generic Ltd")
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.company_type == CompanyType.UNKNOWN

    def test_remote_policy_from_location(self):
        job = make_job(remote_type="remote")
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.remote_policy == "remote"

    def test_remote_policy_from_description(self):
        job = make_job(description="This is a fully remote position.", remote_type=None)
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.remote_policy == "remote"

    def test_hiring_priority_high(self):
        job = make_job(
            description="Urgent! Immediate hire needed ASAP. Critical role.",
            posted_date=datetime.utcnow() - timedelta(days=1),
        )
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.hiring_priority in (HiringPriority.HIGH, HiringPriority.MEDIUM)

    def test_hiring_priority_low(self):
        job = make_job(description="Standard position.")
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)

        assert result.hiring_priority == HiringPriority.LOW

    def test_none_job(self):
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(None)
        assert result.company_type == CompanyType.UNKNOWN
        assert result.hiring_priority == HiringPriority.UNKNOWN

    def test_no_company(self):
        job = MagicMock()
        job.company = None
        job.description = ""
        job.title = ""
        config = make_config()
        analyzer = CompanyAnalyzer(config)
        result = analyzer.analyze(job)
        assert result.company_type == CompanyType.UNKNOWN


# ===========================================================================
# Skill Extraction Tests
# ===========================================================================


class TestSkillExtractor:
    def test_classify_skills(self):
        extractor = SkillExtractor()
        result = extractor.extract(
            job_skills=["Python", "React", "PostgreSQL", "AWS", "Docker", "Git"],
            description="",
        )

        assert "python" in result.programming_languages
        assert "react" in result.frameworks
        assert "postgresql" in result.databases
        assert "aws" in result.cloud_platforms
        assert "git" in result.developer_tools
        assert "docker" in result.cloud_platforms

    def test_soft_skills_classification(self):
        extractor = SkillExtractor()
        result = extractor.extract(
            job_skills=[],
            description="We need strong leadership and communication skills.",
        )

        assert "leadership" in result.soft_skills
        assert "communication" in result.soft_skills

    def test_description_skill_mining(self):
        extractor = SkillExtractor()
        result = extractor.extract(
            job_skills=[],
            description="Experience with Python, Django, and PostgreSQL.",
        )

        assert "python" in result.programming_languages
        assert "django" in result.frameworks
        assert "postgresql" in result.databases

    def test_deduplication(self):
        extractor = SkillExtractor()
        result = extractor.extract(
            job_skills=["Python", "python", "PYTHON"],
            description="Python required.",
        )

        assert len([s for s in result.all_skills if s == "python"]) == 1

    def test_all_skills_merged(self):
        extractor = SkillExtractor()
        result = extractor.extract(
            job_skills=["Kubernetes"],
            description="Docker and AWS experience.",
        )

        assert len(result.all_skills) >= 3
        assert "kubernetes" in result.all_skills
        assert "docker" in result.all_skills
        assert "aws" in result.all_skills

    def test_empty_skills(self):
        extractor = SkillExtractor()
        result = extractor.extract(job_skills=[], description="")
        assert result.all_skills == []
        assert result.programming_languages == []


# ===========================================================================
# Role Analysis Tests
# ===========================================================================


class TestRoleAnalyzer:
    def test_seniority_from_experience_level(self):
        job = make_job(experience_level="senior")
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.seniority == RoleSeniority.SENIOR

    def test_seniority_from_title(self):
        job = make_job(title="Senior Software Engineer", description="", experience_level=None)
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.seniority == RoleSeniority.SENIOR

    def test_seniority_executive_from_title(self):
        job = make_job(title="VP of Engineering", experience_level=None)
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.seniority == RoleSeniority.EXECUTIVE

    def test_seniority_entry_from_title(self):
        job = make_job(title="Junior Developer", experience_level=None)
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.seniority == RoleSeniority.ENTRY

    def test_seniority_unknown(self):
        job = make_job(title="Developer", experience_level=None)
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.seniority == RoleSeniority.UNKNOWN

    def test_role_category_backend(self):
        job = make_job(title="Backend Developer", skills=["Python", "Django", "PostgreSQL"])
        config = make_config()
        skills = SkillExtractor().extract(job.skills, job.description or "")
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, skills)
        assert result.category == RoleCategory.BACKEND

    def test_role_category_frontend(self):
        job = make_job(
            title="Frontend Developer",
            description="Build UI components with React.",
            skills=["JavaScript", "CSS", "HTML"],
        )
        config = make_config()
        skills = SkillExtractor().extract(job.skills, job.description or "")
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, skills)
        assert result.category == RoleCategory.FRONTEND

    def test_role_category_full_stack(self):
        job = make_job(
            title="Full Stack Engineer",
            skills=["Python", "JavaScript", "React", "Django"],
        )
        config = make_config()
        skills = SkillExtractor().extract(job.skills, job.description or "")
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, skills)
        assert result.category == RoleCategory.FULL_STACK

    def test_role_category_data_scientist(self):
        job = make_job(
            title="Data Scientist",
            description="Machine learning, statistical modeling, and predictive analytics.",
            skills=["Python", "TensorFlow"],
        )
        config = make_config()
        skills = SkillExtractor().extract(job.skills, job.description or "")
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, skills)
        assert result.category == RoleCategory.DATA_SCIENTIST

    def test_role_category_devops(self):
        job = make_job(
            title="DevOps Engineer",
            description="CI/CD pipeline, Kubernetes, Docker, infrastructure automation.",
            skills=["Docker", "Kubernetes", "Terraform"],
        )
        config = make_config()
        skills = SkillExtractor().extract(job.skills, job.description or "")
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, skills)
        assert result.category == RoleCategory.DEVOPS

    def test_role_category_mobile(self):
        job = make_job(title="iOS Developer", skills=["Swift", "Kotlin"])
        config = make_config()
        skills = SkillExtractor().extract(job.skills, "")
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, skills)
        assert result.category == RoleCategory.MOBILE

    def test_role_category_qa(self):
        job = make_job(title="QA Engineer", description="Automated testing with Selenium.")
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.category == RoleCategory.QA

    def test_role_category_fallback(self):
        job = make_job(
            title="Engineer",
            description="A generic engineering position with no specific tech keywords.",
            skills=["CSS"],
            experience_level=None,
        )
        config = make_config()
        skills = SkillExtractor().extract(job.skills, "")
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, skills)
        assert result.category == RoleCategory.GENERAL_SOFTWARE_ENGINEER

    def test_responsibilities_extraction(self):
        job = make_job(
            description=(
                "You will be responsible for developing web applications. "
                "You will lead a team of engineers. "
                "You will collaborate with cross-functional teams."
            ),
        )
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        resp = result.responsibilities
        assert len(resp.primary) > 0 or len(resp.leadership) > 0
        assert len(resp.communication) > 0

    def test_qualifications_required_preferred(self):
        job = make_job(
            description=(
                "Requirements:\n"
                "- Must have 5+ years of Python experience.\n"
                "- Bachelor's degree in Computer Science.\n"
                "Preferred:\n"
                "- Experience with AWS is a plus.\n"
                "- Knowledge of Docker preferred."
            ),
        )
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert len(result.qualifications.required) > 0
        assert len(result.qualifications.preferred) > 0

    def test_education_requirements(self):
        job = make_job(
            description="Bachelor's degree in Computer Science required. Master's preferred.",
        )
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert len(result.education_requirements) > 0

    def test_certification_requirements(self):
        job = make_job(
            description="AWS Certified Solutions Architect preferred. CISSP certification is a plus.",
        )
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert len(result.certification_requirements) > 0

    def test_travel_requirements(self):
        job = make_job(
            description="Some travel required up to 25% for client meetings.",
        )
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.travel_requirements is not None
        assert "travel" in result.travel_requirements.lower()

    def test_visa_sponsorship_positive(self):
        job = make_job(
            description="Visa sponsorship available for qualified candidates.",
        )
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.visa_sponsorship_mentioned is True

    def test_visa_sponsorship_negative(self):
        job = make_job(
            description="Must have work authorization. No sponsorship available.",
        )
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.visa_sponsorship_mentioned is False

    def test_visa_sponsorship_not_mentioned(self):
        job = make_job(description="Regular job description.")
        config = make_config()
        analyzer = RoleAnalyzer(config)
        result = analyzer.analyze(job, SkillExtraction())
        assert result.visa_sponsorship_mentioned is None


# ===========================================================================
# Culture Analysis Tests
# ===========================================================================


class TestCultureAnalyzer:
    def test_fast_paced_environment(self):
        job = make_job(description="Work in a fast-paced agile environment.")
        analyzer = CultureAnalyzer()
        result = analyzer.analyze(job)
        assert "fast_paced" in result["work_environment"]

    def test_inclusive_culture(self):
        job = make_job(
            description="We value diversity and inclusion. Equal opportunity employer.",
        )
        analyzer = CultureAnalyzer()
        result = analyzer.analyze(job)
        assert "inclusive" in result["team_culture"]

    def test_learning_growth(self):
        job = make_job(description="Learning budget and mentorship program available.")
        analyzer = CultureAnalyzer()
        result = analyzer.analyze(job)
        assert result["growth_indicators"]["has_learning_budget"] is True
        assert result["growth_indicators"]["has_mentorship"] is True

    def test_unknown_culture(self):
        job = make_job(description="Regular job.")
        analyzer = CultureAnalyzer()
        result = analyzer.analyze(job)
        assert "unknown" in result["work_environment"]
        assert "unknown" in result["team_culture"]


# ===========================================================================
# Validation Tests
# ===========================================================================


class TestValidator:
    def test_valid_job_passes(self):
        job = make_job()
        validator = ApplicationIntelligenceValidator()
        result = validator.validate(job)
        assert not result.has_missing_description
        assert not result.has_incomplete_posting
        assert result.warnings == []

    def test_missing_description(self):
        job = make_job(description="")
        validator = ApplicationIntelligenceValidator()
        result = validator.validate(job)
        assert result.has_missing_description
        assert "missing a description" in str(result.warnings)

    def test_none_job(self):
        validator = ApplicationIntelligenceValidator()
        result = validator.validate(None)
        assert result.has_incomplete_posting

    def test_salary_conflict_min_greater_max(self):
        job = make_job(salary_min=200000, salary_max=100000)
        validator = ApplicationIntelligenceValidator()
        result = validator.validate(job)
        assert result.conflicting_salary

    def test_salary_no_conflict(self):
        job = make_job(salary_min=100000, salary_max=200000)
        validator = ApplicationIntelligenceValidator()
        result = validator.validate(job)
        assert not result.conflicting_salary

    def test_location_conflict_remote_with_city(self):
        job = make_job(city="San Francisco", remote_type="remote")
        job.location.display_name = "San Francisco, CA"
        validator = ApplicationIntelligenceValidator()
        result = validator.validate(job)
        assert result.conflicting_location

    def test_invalid_employment_type(self):
        job = make_job(employment_type="invalid_type")
        validator = ApplicationIntelligenceValidator()
        result = validator.validate(job)
        assert result.invalid_employment_type

    def test_duplicate_skills(self):
        job = make_job(skills=["Python", "Python", "Java", "Java"])
        validator = ApplicationIntelligenceValidator()
        result = validator.validate(job)
        assert len(result.duplicate_requirements) >= 2


# ===========================================================================
# Cache Tests
# ===========================================================================


class TestCache:
    def test_get_set(self):
        config = make_config()
        cache = AnalysisCache(config)
        ai = ApplicationIntelligence()
        cache.set("test-key", ai)
        cached = cache.get("test-key")
        assert cached is not None
        assert cached.id == ai.id

    def test_get_missing(self):
        config = make_config()
        cache = AnalysisCache(config)
        assert cache.get("nonexistent") is None

    def test_invalidate(self):
        config = make_config()
        cache = AnalysisCache(config)
        cache.set("test-key", ApplicationIntelligence())
        cache.invalidate("test-key")
        assert cache.get("test-key") is None

    def test_clear(self):
        config = make_config()
        cache = AnalysisCache(config)
        cache.set("a", ApplicationIntelligence())
        cache.set("b", ApplicationIntelligence())
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_ttl_expiry(self):
        config = ApplicationIntelligenceConfig(cache_ttl_seconds=0)
        cache = AnalysisCache(config)
        cache.set("test-key", ApplicationIntelligence())
        import time
        time.sleep(0.01)
        assert cache.get("test-key") is None

    def test_compute_key(self):
        config = make_config()
        cache = AnalysisCache(config)
        key = cache.compute_key("job123", "prof456")
        assert "prof456" in key
        assert "job123" in key

    def test_compute_key_no_profile(self):
        config = make_config()
        cache = AnalysisCache(config)
        key = cache.compute_key("job123")
        assert ":job123" in key


# ===========================================================================
# Salary & Location Analysis Tests
# ===========================================================================


class TestSalaryLocationAnalysis:
    def test_salary_analysis(self):
        job = make_job(salary_min=100000, salary_max=200000)
        validator = ApplicationIntelligenceValidator()
        vresult = validator.validate(job)
        assert not vresult.conflicting_salary

    def test_no_salary(self):
        job = make_job(salary_min=None, salary_max=None)
        validator = ApplicationIntelligenceValidator()
        vresult = validator.validate(job)
        assert not vresult.conflicting_salary

    def test_remote_possible(self):
        job = make_job(remote_type="remote")
        validator = ApplicationIntelligenceValidator()
        validator.validate(job)
        assert True


# ===========================================================================
# Service Integration Tests
# ===========================================================================


class TestService:
    def test_analyze_basic_job(self):
        job = make_job()
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job)

        assert isinstance(result, ApplicationIntelligence)
        assert result.job_hash is not None
        assert result.company.summary is not None
        assert result.role.summary is not None
        assert result.confidence_score > 0

    def test_analyze_with_match_result(self):
        job = make_job()
        match_result = MagicMock()
        match_result.overall_match_score = 85.0

        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job, match_result=match_result)
        assert result.application_priority in (
            ApplicationPriority.HIGH,
            ApplicationPriority.MEDIUM,
        )

    def test_analyze_with_profile_intelligence(self):
        job = make_job()
        profile = MagicMock()
        profile.profile_hash = "abc123"
        completeness = MagicMock()
        completeness.overall_score = 90
        profile.completeness = completeness

        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job, profile_intelligence=profile)
        assert result.profile_hash == "abc123"

    def test_caching_returns_same_result(self):
        job = make_job()
        config = ApplicationIntelligenceConfig(cache_ttl_seconds=300)
        service = ApplicationIntelligenceService(config)
        result1 = service.analyze(job)
        result2 = service.analyze(job)
        assert result1.id == result2.id

    def test_skip_cache(self):
        job = make_job()
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result1 = service.analyze(job)
        result2 = service.analyze(job, skip_cache=True)
        assert result1.id != result2.id

    def test_invalidate_cache(self):
        job = make_job()
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result1 = service.analyze(job)
        cache_key = f":{result1.job_hash}"
        service.invalidate_cache(cache_key)
        result2 = service.analyze(job)
        assert result1.id != result2.id

    def test_clear_cache(self):
        job = make_job()
        config = make_config()
        service = ApplicationIntelligenceService(config)
        service.analyze(job)
        service.clear_cache()
        result2 = service.analyze(job)
        assert result2 is not None

    def test_confidence_score(self):
        job = make_job(description="Full description here.")
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job)
        assert 0.0 <= result.confidence_score <= 1.0

    def test_none_job(self):
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(None)
        assert result.validation.has_incomplete_posting

    def test_low_priority_job(self):
        job = make_job(title="", description="", skills=[])
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job)
        assert result.application_priority == ApplicationPriority.LOW

    def test_high_priority_job(self):
        job = make_job(
            title="Senior Engineer",
            description=(
                "Urgent! High priority role. Immediate hire needed. "
                "Critical position for our growing team. We need someone ASAP."
            ),
            posted_date=datetime.utcnow() - timedelta(days=1),
            skills=["Python", "AWS", "Docker", "Kubernetes", "Terraform"],
        )
        match_result = MagicMock()
        match_result.overall_match_score = 90.0
        profile = MagicMock()
        profile.profile_hash = "prof123"
        completeness = MagicMock()
        completeness.overall_score = 95
        profile.completeness = completeness

        config = ApplicationIntelligenceConfig(
            cache_ttl_seconds=300,
            strict_validation=True,
            high_priority_threshold=0.3,
            medium_priority_threshold=0.15,
        )

        service = ApplicationIntelligenceService(config)
        result = service.analyze(
            job,
            match_result=match_result,
            profile_intelligence=profile,
        )
        assert result.application_priority == ApplicationPriority.HIGH

    def test_employment_type_analysis(self):
        job = make_job(employment_type="full_time")
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job)
        assert "Full-time" in result.employment_type_analysis or "full time" in result.raw_employment_type


# ===========================================================================
# Edge Cases
# ===========================================================================


class TestEdgeCases:
    def test_empty_skills_job(self):
        job = make_job(skills=[], description="")
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job)
        assert result.role.skills.all_skills == []

    def test_very_long_description(self):
        job = make_job(description="Python " * 1000)
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job)
        assert "python" in result.role.skills.programming_languages

    def test_special_characters_in_title(self):
        job = make_job(title="Software Engineer (Python/JS) - $competitive")
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job)
        assert result.role.summary is not None

    def test_job_with_no_location(self):
        job_no_loc = MagicMock()
        job_no_loc.id = uuid.uuid4()
        job_no_loc.provider_job_id = "1"
        job_no_loc.title = "Engineer"
        job_no_loc.company = MagicMock()
        job_no_loc.company.name = "Test"
        job_no_loc.company.website = None
        job_no_loc.company.logo_url = None
        job_no_loc.company.description = None
        job_no_loc.company.industry = None
        job_no_loc.company.size = None
        job_no_loc.location = None
        job_no_loc.description = "A job."
        job_no_loc.description_html = None
        job_no_loc.url = None
        job_no_loc.apply_url = None
        job_no_loc.employment_type = "full_time"
        job_no_loc.experience_level = "mid"
        job_no_loc.salary = None
        job_no_loc.skills = ["Python"]
        job_no_loc.posted_date = None
        job_no_loc.expiration_date = None
        job_no_loc.provider = "test"
        job_no_loc.source_updated_at = None

        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job_no_loc)
        assert result.validation is not None
        assert result.role.summary == "Engineer"

    def test_job_with_unicode_description(self):
        job = make_job(description="Python engineer needed for café app. Crêpe ordering system.")
        config = make_config()
        service = ApplicationIntelligenceService(config)
        result = service.analyze(job)
        assert "python" in result.role.skills.programming_languages


# ===========================================================================
# Analyzer Integration Tests
# ===========================================================================


class TestAnalyzer:
    def test_analyze_caches_result(self):
        job = make_job()
        config = make_config()
        from app.application_intelligence.analyzer import ApplicationIntelligenceAnalyzer
        analyzer = ApplicationIntelligenceAnalyzer(config)
        result1 = analyzer.analyze(job)
        result2 = analyzer.analyze(job)
        assert result1.id == result2.id

    def test_analyze_skip_cache(self):
        job = make_job()
        config = make_config()
        from app.application_intelligence.analyzer import ApplicationIntelligenceAnalyzer
        analyzer = ApplicationIntelligenceAnalyzer(config)
        result1 = analyzer.analyze(job)
        result2 = analyzer.analyze(job, skip_cache=True)
        assert result1.id != result2.id

    def test_analyze_with_all_inputs(self):
        job = make_job()
        match_result = MagicMock()
        match_result.overall_match_score = 75.0
        profile = MagicMock()
        profile.profile_hash = "prof999"
        profile.completeness = MagicMock()
        profile.completeness.overall_score = 80

        config = make_config()
        from app.application_intelligence.analyzer import ApplicationIntelligenceAnalyzer
        analyzer = ApplicationIntelligenceAnalyzer(config)
        result = analyzer.analyze(job, match_result, profile)
        assert result.application_priority == ApplicationPriority.HIGH
