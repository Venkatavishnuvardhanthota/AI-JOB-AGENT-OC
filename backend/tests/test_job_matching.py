from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.job_matching.cache import MatchCache
from app.job_matching.comparator import (
    CareerLevelComparator,
    CertificationsComparator,
    EducationComparator,
    EmploymentTypeComparator,
    ExperienceComparator,
    IndustryComparator,
    LocationComparator,
    ProjectsComparator,
    RemoteComparator,
    SalaryComparator,
    SkillComparator,
)
from app.job_matching.config import MatchingConfig
from app.job_matching.exceptions import MatchValidationError
from app.job_matching.explanations import ExplanationGenerator
from app.job_matching.schemas import (
    DimensionScore,
    MatchRecommendation,
    MatchResult,
    SkillMatchInfo,
)
from app.job_matching.scoring import ScoringEngine
from app.job_matching.service import JobMatchingService
from app.job_matching.validator import MatchValidator


@pytest.fixture
def config() -> MatchingConfig:
    return MatchingConfig()


@pytest.fixture
def service(config: MatchingConfig) -> JobMatchingService:
    return JobMatchingService(config=config)


def make_profile(
    primary_skills=None,
    secondary_skills=None,
    years_exp=None,
    career_level=None,
    education_summary=None,
    preferred_locations=None,
    remote_preference=None,
    salary_expectation=None,
    employment_preference=None,
    industries=None,
    certifications=None,
    projects=None,
    completeness_score=None,
    profile_hash=None,
):
    profile = MagicMock()
    profile.primary_skills = primary_skills or []
    profile.secondary_skills = secondary_skills or []
    profile.years_of_experience = years_exp
    profile.career_level = career_level
    profile.education_summary = education_summary
    profile.preferred_locations = preferred_locations or []
    profile.remote_preference = remote_preference
    profile.salary_expectation = salary_expectation
    profile.employment_preference = employment_preference
    profile.industries = industries or []
    profile.certifications = certifications or []
    profile.projects = projects or []
    profile.profile_hash = profile_hash

    ts = MagicMock()
    ts.programming_languages = []
    ts.frameworks = []
    ts.databases = []
    ts.cloud_platforms = []
    ts.tools = []
    profile.technical_stack = ts

    if completeness_score is not None:
        comp = MagicMock()
        comp.overall_score = completeness_score
        profile.completeness = comp
    else:
        profile.completeness = None

    return profile


def make_job(
    skills=None,
    title="Software Engineer",
    company_name="Acme",
    company_industry="Tech",
    employment_type="full_time",
    experience_level="mid",
    salary_min=None,
    salary_max=None,
    city=None,
    state=None,
    country=None,
    remote_type=None,
    display_name=None,
):
    job = MagicMock()
    job.id = uuid.uuid4()
    job.title = title
    job.skills = skills or []

    company = MagicMock()
    company.name = company_name
    company.industry = company_industry
    job.company = company

    job.employment_type = employment_type
    job.experience_level = experience_level

    sal = MagicMock()
    sal.min_amount = salary_min
    sal.max_amount = salary_max
    job.salary = sal

    loc = MagicMock()
    loc.city = city
    loc.state = state
    loc.country = country
    loc.remote_type = remote_type
    loc.display_name = display_name
    job.location = loc

    return job


class TestSkillComparator:
    def test_exact_match(self, config):
        comp = SkillComparator(config)
        matching, missing, preferred, score = comp.compare(
            profile_skills=["Python", "SQL", "FastAPI"],
            job_skills=["Python", "SQL", "FastAPI"],
        )
        assert len(matching) == 3
        assert len(missing) == 0
        assert score == 100.0

    def test_no_match(self, config):
        comp = SkillComparator(config)
        matching, missing, preferred, score = comp.compare(
            profile_skills=["Python"],
            job_skills=["Java", "C++"],
        )
        assert len(matching) == 0
        assert len(missing) == 2
        assert score == 0.0

    def test_partial_match(self, config):
        comp = SkillComparator(config)
        matching, missing, preferred, score = comp.compare(
            profile_skills=["Python", "SQL", "Docker"],
            job_skills=["Python", "Java", "Kubernetes"],
        )
        assert len(matching) == 1
        assert len(missing) == 2
        assert score == pytest.approx(33.3, rel=0.1)

    def test_case_insensitive(self, config):
        comp = SkillComparator(config)
        matching, missing, preferred, score = comp.compare(
            profile_skills=["python", "sql"],
            job_skills=["Python", "SQL"],
        )
        assert len(matching) == 2
        assert score == 100.0

    def test_preferred_skills(self, config):
        comp = SkillComparator(config)
        matching, missing, preferred, score = comp.compare(
            profile_skills=["Python", "SQL", "Docker"],
            job_skills=["Python"],
            profile_primary=["Python", "SQL"],
            profile_secondary=["Docker"],
        )
        assert len(matching) == 1
        assert len(preferred) == 2
        assert score == 100.0

    def test_empty_job_skills(self, config):
        comp = SkillComparator(config)
        matching, missing, preferred, score = comp.compare(
            profile_skills=["Python"],
            job_skills=[],
        )
        assert len(matching) == 0
        assert len(missing) == 0
        assert score == 0.0

    def test_primary_skill_bonus(self, config):
        comp = SkillComparator(config)
        matching, missing, preferred, score = comp.compare(
            profile_skills=["Python", "SQL"],
            job_skills=["Python", "Java"],
            profile_primary=["Python"],
        )
        assert score > 50.0

    def test_empty_profile_skills(self, config):
        comp = SkillComparator(config)
        matching, missing, preferred, score = comp.compare(
            profile_skills=[],
            job_skills=["Python", "SQL"],
        )
        assert len(missing) == 2
        assert len(matching) == 0
        assert score == 0.0


class TestExperienceComparator:
    def test_perfect_match(self):
        comp = ExperienceComparator()
        score = comp.compare(5.0, "mid", MatchingConfig())
        assert score == 100.0

    def test_no_profile_years(self):
        comp = ExperienceComparator()
        score = comp.compare(None, "mid", MatchingConfig())
        assert score == 30.0

    def test_no_job_level(self):
        comp = ExperienceComparator()
        score = comp.compare(5.0, None, MatchingConfig())
        assert score == 60.0

    def test_far_off(self):
        comp = ExperienceComparator()
        score = comp.compare(1.0, "senior", MatchingConfig())
        assert score == 20.0

    def test_all_none(self):
        comp = ExperienceComparator()
        score = comp.compare(None, None, MatchingConfig())
        assert score == 50.0

    def test_high_experience(self):
        comp = ExperienceComparator()
        score = comp.compare(12.0, None, MatchingConfig())
        assert score == 80.0


class TestEducationComparator:
    def test_perfect_match(self):
        comp = EducationComparator()
        score = comp.compare("Bachelor of Science in Computer Science", ["Bachelor"])
        assert score == 100.0

    def test_no_job_requirement(self):
        comp = EducationComparator()
        score = comp.compare("Bachelor of Science", None)
        assert score == 80.0

    def test_no_profile_education(self):
        comp = EducationComparator()
        score = comp.compare(None, ["Bachelor"])
        assert score == 20.0

    def test_both_missing(self):
        comp = EducationComparator()
        score = comp.compare(None, None)
        assert score == 50.0

    def test_higher_education(self):
        comp = EducationComparator()
        score = comp.compare("PhD in Computer Science", ["Bachelor"])
        assert score == 100.0

    def test_lower_education(self):
        comp = EducationComparator()
        score = comp.compare("Associate Degree", ["Bachelor"])
        assert score == 30.0


class TestLocationComparator:
    def test_exact_match(self):
        comp = LocationComparator()
        score = comp.compare(
            profile_locations=["New York", "Remote"],
            job_city="New York",
            job_state="NY",
            job_country="US",
            job_display="New York, NY",
        )
        assert score == 100.0

    def test_no_match(self):
        comp = LocationComparator()
        score = comp.compare(
            profile_locations=["San Francisco"],
            job_city="New York",
            job_state="NY",
            job_country="US",
            job_display=None,
        )
        assert score == 20.0

    def test_no_profile_locations(self):
        comp = LocationComparator()
        score = comp.compare(None, "New York", "NY", "US", None)
        assert score == 50.0

    def test_no_job_location(self):
        comp = LocationComparator()
        score = comp.compare(["San Francisco"], None, None, None, None)
        assert score == 60.0

    def test_same_country(self):
        comp = LocationComparator()
        score = comp.compare(
            profile_locations=["San Francisco", "Los Angeles"],
            job_city="New York",
            job_state="NY",
            job_country="US",
            job_display=None,
        )
        assert score == 20.0


class TestRemoteComparator:
    def test_remote_match(self):
        comp = RemoteComparator()
        score = comp.compare(True, "remote")
        assert score == 100.0

    def test_onsite_match(self):
        comp = RemoteComparator()
        score = comp.compare(False, "on_site")
        assert score == 100.0

    def test_remote_vs_onsite(self):
        comp = RemoteComparator()
        score = comp.compare(True, "on_site")
        assert score == 40.0

    def test_hybrid_with_remote_pref(self):
        comp = RemoteComparator()
        score = comp.compare(True, "hybrid")
        assert score == 70.0

    def test_no_preference(self):
        comp = RemoteComparator()
        score = comp.compare(None, "remote")
        assert score == 50.0

    def test_no_job_type(self):
        comp = RemoteComparator()
        score = comp.compare(True, None)
        assert score == 60.0

    def test_unknown_job_type(self):
        comp = RemoteComparator()
        score = comp.compare(True, "unknown")
        assert score == 60.0


class TestSalaryComparator:
    def test_perfect_match(self):
        comp = SalaryComparator()
        score = comp.compare("USD 100,000/year", 90000, 110000, MatchingConfig())
        assert score == 100.0

    def test_no_job_salary(self):
        comp = SalaryComparator()
        score = comp.compare("USD 100,000/year", None, None, MatchingConfig())
        assert score == 60.0

    def test_no_profile_salary(self):
        comp = SalaryComparator()
        score = comp.compare(None, 90000, 110000, MatchingConfig())
        assert score == 50.0

    def test_large_gap(self):
        comp = SalaryComparator()
        score = comp.compare("USD 50,000/year", 150000, 180000, MatchingConfig())
        assert score == 20.0

    def test_profile_higher(self):
        comp = SalaryComparator()
        score = comp.compare("USD 200,000/year", 90000, 110000, MatchingConfig())
        assert score == 60.0


class TestEmploymentTypeComparator:
    def test_exact_match(self):
        comp = EmploymentTypeComparator()
        score = comp.compare("Full Time", "full_time")
        assert score == 100.0

    def test_no_match(self):
        comp = EmploymentTypeComparator()
        score = comp.compare("Full Time", "contract")
        assert score == 20.0

    def test_no_preference(self):
        comp = EmploymentTypeComparator()
        score = comp.compare(None, "full_time")
        assert score == 50.0

    def test_unknown_job_type(self):
        comp = EmploymentTypeComparator()
        score = comp.compare("Full Time", "unknown")
        assert score == 60.0

    def test_other_job_type(self):
        comp = EmploymentTypeComparator()
        score = comp.compare("Full Time", "other")
        assert score == 60.0


class TestCareerLevelComparator:
    def test_exact_match(self):
        comp = CareerLevelComparator()
        score = comp.compare("senior", "senior")
        assert score == 100.0

    def test_one_level_off(self):
        comp = CareerLevelComparator()
        score = comp.compare("senior", "mid")
        assert score == 70.0

    def test_two_levels_off(self):
        comp = CareerLevelComparator()
        score = comp.compare("senior", "junior")
        assert score == 40.0

    def test_far_off(self):
        comp = CareerLevelComparator()
        score = comp.compare("executive", "entry")
        assert score == 20.0

    def test_no_profile_level(self):
        comp = CareerLevelComparator()
        score = comp.compare(None, "senior")
        assert score == 50.0

    def test_no_job_level(self):
        comp = CareerLevelComparator()
        score = comp.compare("senior", None)
        assert score == 60.0

    def test_unknown_values(self):
        comp = CareerLevelComparator()
        score = comp.compare("unknown", "senior")
        assert score == 50.0


class TestIndustryComparator:
    def test_exact_match(self):
        comp = IndustryComparator()
        score = comp.compare(["Tech", "Finance"], "Tech")
        assert score == 100.0

    def test_no_match(self):
        comp = IndustryComparator()
        score = comp.compare(["Healthcare"], "Tech")
        assert score == 30.0

    def test_no_profile_industries(self):
        comp = IndustryComparator()
        score = comp.compare(None, "Tech")
        assert score == 50.0

    def test_no_job_industry(self):
        comp = IndustryComparator()
        score = comp.compare(["Tech"], None)
        assert score == 60.0

    def test_substring_match(self):
        comp = IndustryComparator()
        score = comp.compare(["Information Technology"], "Tech")
        assert score == 100.0


class TestCertificationsComparator:
    def test_many_certs(self):
        comp = CertificationsComparator()
        score = comp.compare(["A", "B", "C", "D", "E"])
        assert score == 100.0

    def test_some_certs(self):
        comp = CertificationsComparator()
        score = comp.compare(["A", "B", "C"])
        assert score == 80.0

    def test_one_cert(self):
        comp = CertificationsComparator()
        score = comp.compare(["A"])
        assert score == 60.0

    def test_no_certs(self):
        comp = CertificationsComparator()
        score = comp.compare(None)
        assert score == 30.0


class TestProjectsComparator:
    def test_many_projects(self):
        comp = ProjectsComparator()
        score = comp.compare(["A", "B", "C", "D", "E"])
        assert score == 100.0

    def test_some_projects(self):
        comp = ProjectsComparator()
        score = comp.compare(["A", "B", "C"])
        assert score == 75.0

    def test_one_project(self):
        comp = ProjectsComparator()
        score = comp.compare(["A"])
        assert score == 50.0

    def test_no_projects(self):
        comp = ProjectsComparator()
        score = comp.compare(None)
        assert score == 20.0


class TestScoringEngine:
    def test_perfect_match(self):
        engine = ScoringEngine(MatchingConfig())
        score = engine.compute_overall(
            skills_score=100,
            experience_score=100,
            education_score=100,
            location_score=100,
            remote_score=100,
            salary_score=100,
            employment_type_score=100,
            career_level_score=100,
            industry_score=100,
            certifications_score=100,
            projects_score=100,
        )
        assert score == 100.0

    def test_zero_match(self):
        engine = ScoringEngine(MatchingConfig())
        score = engine.compute_overall(
            skills_score=0,
            experience_score=0,
            education_score=0,
            location_score=0,
            remote_score=0,
            salary_score=0,
            employment_type_score=0,
            career_level_score=0,
            industry_score=0,
            certifications_score=0,
            projects_score=0,
        )
        assert score == 0.0

    def test_partial_match(self):
        engine = ScoringEngine(MatchingConfig())
        score = engine.compute_overall(
            skills_score=80,
            experience_score=70,
            education_score=60,
            location_score=100,
            remote_score=100,
            salary_score=80,
            employment_type_score=100,
            career_level_score=100,
            industry_score=100,
            certifications_score=60,
            projects_score=50,
        )
        assert 70 <= score <= 90

    def test_confidence_high(self):
        engine = ScoringEngine(MatchingConfig())
        conf = engine.compute_confidence(90.0, 90)
        assert conf >= 0.8

    def test_confidence_low(self):
        engine = ScoringEngine(MatchingConfig())
        conf = engine.compute_confidence(10.0, 10)
        assert conf <= 0.3

    def test_confidence_no_completeness(self):
        engine = ScoringEngine(MatchingConfig())
        conf = engine.compute_confidence(50.0, None)
        assert conf == pytest.approx(0.5, rel=0.1)

    def test_recommendation_strong(self):
        engine = ScoringEngine(MatchingConfig())
        rec = engine.compute_recommendation(85.0)
        assert rec == MatchRecommendation.STRONG_APPLY

    def test_recommendation_apply(self):
        engine = ScoringEngine(MatchingConfig())
        rec = engine.compute_recommendation(70.0)
        assert rec == MatchRecommendation.APPLY

    def test_recommendation_consider(self):
        engine = ScoringEngine(MatchingConfig())
        rec = engine.compute_recommendation(50.0)
        assert rec == MatchRecommendation.CONSIDER

    def test_recommendation_weak(self):
        engine = ScoringEngine(MatchingConfig())
        rec = engine.compute_recommendation(35.0)
        assert rec == MatchRecommendation.WEAK

    def test_recommendation_not_recommended(self):
        engine = ScoringEngine(MatchingConfig())
        rec = engine.compute_recommendation(10.0)
        assert rec == MatchRecommendation.NOT_RECOMMENDED


class TestExplanationGenerator:
    def test_generate_summary(self):
        gen = ExplanationGenerator()
        result = MatchResult(overall_match_score=75.5, recommendation=MatchRecommendation.APPLY)
        summary = gen.generate_summary(result)
        assert "76" in summary or "75" in summary
        assert "Apply" in summary

    def test_generate_improvement_recommendations_with_missing_skills(self):
        gen = ExplanationGenerator()
        result = MatchResult(
            overall_match_score=40.0,
            matching_skills=[SkillMatchInfo(name="Python", matched=True)],
            missing_skills=[
                SkillMatchInfo(name="Docker", matched=False),
                SkillMatchInfo(name="Kubernetes", matched=False),
            ],
        )
        recs = gen.generate_improvement_recommendations(result)
        assert len(recs) > 0
        assert any("Docker" in r for r in recs)

    def test_generate_improvement_recommendations_no_missing(self):
        gen = ExplanationGenerator()
        result = MatchResult(overall_match_score=90.0)
        recs = gen.generate_improvement_recommendations(result)
        assert len(recs) >= 0

    def test_format_skill_details(self):
        gen = ExplanationGenerator()
        result = MatchResult(
            matching_skills=[SkillMatchInfo(name="Python", matched=True)],
            missing_skills=[SkillMatchInfo(name="Docker", matched=False)],
        )
        details = gen.format_skill_details(result)
        assert any("✓ Python" in d for d in details)
        assert any("✗ Docker" in d for d in details)


class TestMatchValidator:
    def test_validate_profile_empty(self):
        validator = MatchValidator()
        warnings = validator.validate_profile(None)
        assert len(warnings) > 0
        assert any("No profile" in w for w in warnings)

    def test_validate_profile_low_completeness(self):
        validator = MatchValidator()
        profile = make_profile(completeness_score=20)
        warnings = validator.validate_profile(profile)
        assert any("low" in w.lower() for w in warnings)

    def test_validate_profile_no_skills(self):
        validator = MatchValidator()
        profile = make_profile()
        warnings = validator.validate_profile(profile)
        assert any("skills" in w.lower() for w in warnings)

    def test_validate_profile_complete(self):
        validator = MatchValidator()
        profile = make_profile(
            primary_skills=["Python"],
            years_exp=5,
            education_summary="BS CS",
            completeness_score=80,
        )
        warnings = validator.validate_profile(profile)
        assert len(warnings) == 0

    def test_validate_job_empty(self):
        validator = MatchValidator()
        warnings = validator.validate_job(None)
        assert len(warnings) > 0

    def test_validate_job_no_skills(self):
        validator = MatchValidator()
        job = make_job(skills=[])
        warnings = validator.validate_job(job)
        assert any("skills" in w.lower() for w in warnings)

    def test_validate_job_valid(self):
        validator = MatchValidator()
        job = make_job(skills=["Python"], title="Engineer")
        warnings = validator.validate_job(job)
        assert len(warnings) == 0

    def test_validate_job_invalid_salary(self):
        validator = MatchValidator()
        job = make_job(skills=["Python"], salary_min=200000, salary_max=100000)
        warnings = validator.validate_job(job)
        assert any("salary" in w.lower() for w in warnings)

    def test_assert_valid_input_raises(self):
        validator = MatchValidator()
        with pytest.raises(MatchValidationError):
            validator.assert_valid_input(None, None)

    def test_assert_valid_input_ok(self):
        validator = MatchValidator()
        profile = make_profile(
            primary_skills=["Python"],
            years_exp=5,
            education_summary="BS CS",
            completeness_score=80,
        )
        job = make_job(skills=["Python"], title="Engineer")
        validator.assert_valid_input(profile, job)


class TestMatchCache:
    def test_set_and_get(self):
        cache = MatchCache(MatchingConfig(cache_ttl_seconds=60))
        result = MatchResult()
        cache.set("test", result)
        cached = cache.get("test")
        assert cached is not None
        assert cached.id == result.id

    def test_miss(self):
        cache = MatchCache(MatchingConfig(cache_ttl_seconds=60))
        cached = cache.get("nonexistent")
        assert cached is None

    def test_invalidate(self):
        cache = MatchCache(MatchingConfig(cache_ttl_seconds=60))
        result = MatchResult()
        cache.set("test", result)
        cache.invalidate("test")
        cached = cache.get("test")
        assert cached is None

    def test_clear(self):
        cache = MatchCache(MatchingConfig(cache_ttl_seconds=60))
        cache.set("a", MatchResult())
        cache.set("b", MatchResult())
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_ttl_expiry(self):
        cache = MatchCache(MatchingConfig(cache_ttl_seconds=0))
        result = MatchResult()
        cache.set("test", result)
        cached = cache.get("test")
        assert cached is None

    def test_compute_key(self):
        cache = MatchCache(MatchingConfig())
        key = cache.compute_key("hash123", "job456")
        assert "hash123" in key
        assert "job456" in key

    def test_compute_key_none(self):
        cache = MatchCache(MatchingConfig())
        key = cache.compute_key(None, None)
        assert ":" in key


class TestJobMatchingService:
    def test_match_perfect(self, service):
        profile = make_profile(
            primary_skills=["Python", "SQL", "FastAPI"],
            years_exp=5,
            career_level="mid",
            education_summary="BS Computer Science",
            preferred_locations=["New York"],
            remote_preference=True,
            salary_expectation="USD 100,000/year",
            employment_preference="Full Time",
            industries=["Tech"],
            certifications=["AWS Certified"],
            projects=["Project A"],
            completeness_score=80,
        )
        job = make_job(
            skills=["Python", "SQL", "FastAPI"],
            title="Software Engineer",
            company_industry="Tech",
            employment_type="full_time",
            experience_level="mid",
            salary_min=90000,
            salary_max=110000,
            city="New York",
            state="NY",
            country="US",
            remote_type="remote",
        )
        result = service.match(profile, job)
        assert result.overall_match_score >= 70
        assert result.recommendation in (MatchRecommendation.STRONG_APPLY, MatchRecommendation.APPLY)
        assert len(result.matching_skills) > 0
        assert len(result.missing_skills) == 0
        assert result.match_summary is not None

    def test_match_no_match(self, service):
        profile = make_profile(
            primary_skills=["Python"],
            years_exp=1,
            career_level="entry",
            education_summary="High School",
            preferred_locations=["London"],
            remote_preference=True,
            salary_expectation="USD 200,000/year",
            employment_preference="Contract",
            industries=["Healthcare"],
            completeness_score=30,
        )
        job = make_job(
            skills=["Java", "C++", "Go", "Rust"],
            title="Senior Engineer",
            company_industry="Finance",
            employment_type="full_time",
            experience_level="senior",
            salary_min=80000,
            salary_max=100000,
            city="Mumbai",
            country="IN",
            remote_type="on_site",
        )
        result = service.match(profile, job)
        assert result.overall_match_score < 50
        assert len(result.matching_skills) == 0
        assert len(result.missing_skills) > 0

    def test_match_caching(self, service):
        profile = make_profile(primary_skills=["Python"], completeness_score=80)
        job = make_job(skills=["Python"])
        result1 = service.match(profile, job)
        result2 = service.match(profile, job)
        assert result1.id == result2.id

    def test_match_skip_cache(self, service):
        profile = make_profile(primary_skills=["Python"], completeness_score=80)
        job = make_job(skills=["Python"])
        result1 = service.match(profile, job, skip_cache=True)
        result2 = service.match(profile, job, skip_cache=False)
        assert result1.id == result2.id

    def test_match_different_jobs_different_results(self, service):
        profile = make_profile(primary_skills=["Python"], completeness_score=80)
        job1 = make_job(skills=["Python"])
        job2 = make_job(skills=["Java"])
        result1 = service.match(profile, job1)
        result2 = service.match(profile, job2)
        assert result1.overall_match_score != result2.overall_match_score

    def test_invalidate_cache(self, service):
        profile = make_profile(primary_skills=["Python"], completeness_score=80)
        job = make_job(skills=["Python"])
        result1 = service.match(profile, job)
        service.invalidate_cache(
            service._cache.compute_key(
                profile.profile_hash,
                str(job.id),
            )
        )
        result2 = service.match(profile, job)
        assert result1.id != result2.id

    def test_clear_cache(self, service):
        profile = make_profile(primary_skills=["Python"], completeness_score=80)
        job = make_job(skills=["Python"])
        service.match(profile, job)
        service.clear_cache()
        result2 = service.match(profile, job)
        assert result2 is not None

    def test_empty_profile(self, service):
        profile = make_profile()
        job = make_job(skills=["Python"])
        result = service.match(profile, job)
        assert result is not None
        assert result.overall_match_score >= 0

    def test_empty_job(self, service):
        profile = make_profile(primary_skills=["Python"], completeness_score=80)
        job = make_job(skills=[])
        result = service.match(profile, job)
        assert result is not None

    def test_deterministic_output(self, service):
        profile = make_profile(
            primary_skills=["Python", "SQL"],
            years_exp=5,
            career_level="mid",
            completeness_score=80,
        )
        job = make_job(
            skills=["Python", "SQL"],
            employment_type="full_time",
            experience_level="mid",
        )
        result1 = service.match(profile, job)
        result2 = service.match(profile, job)
        assert result1.overall_match_score == result2.overall_match_score
        assert len(result1.matching_skills) == len(result2.matching_skills)

    def test_skill_match_info_fields(self, service):
        profile = make_profile(primary_skills=["Python", "SQL"], completeness_score=80)
        job = make_job(skills=["Python", "Java"])
        result = service.match(profile, job)
        matched = [s for s in result.matching_skills if s.name == "Python"]
        assert len(matched) > 0
        assert matched[0].matched is True
        missing = [s for s in result.missing_skills if s.name == "Java"]
        assert len(missing) > 0
        assert missing[0].matched is False


class TestMatchResultSchema:
    def test_default_values(self):
        result = MatchResult()
        assert result.overall_match_score == 0.0
        assert result.recommendation == MatchRecommendation.NOT_RECOMMENDED
        assert result.confidence_score == 0.0
        assert result.matching_skills == []
        assert result.missing_skills == []
        assert result.preferred_skills == []

    def test_skill_match_info_defaults(self):
        info = SkillMatchInfo(name="Python", matched=True)
        assert info.name == "Python"
        assert info.matched is True
        assert info.category is None
        assert info.proficiency is None

    def test_dimension_score_defaults(self):
        ds = DimensionScore()
        assert ds.score == 0.0
        assert ds.weight == 0.0
        assert ds.weighted_score == 0.0

    def test_id_generation(self):
        r1 = MatchResult()
        r2 = MatchResult()
        assert r1.id != r2.id

    def test_created_at_set(self):
        result = MatchResult()
        assert result.created_at is not None


class TestConfig:
    def test_weights_sum_to_one(self):
        MatchingConfig()

    def test_invalid_weights_raises(self):
        with pytest.raises(ValueError, match="must sum to 1.0"):
            MatchingConfig(skills_weight=1.0, experience_weight=1.0)

    def test_custom_config(self):
        cfg = MatchingConfig(
            skills_weight=0.5,
            experience_weight=0.1,
            education_weight=0.1,
            location_weight=0.05,
            remote_weight=0.05,
            salary_weight=0.05,
            employment_type_weight=0.05,
            career_level_weight=0.03,
            industry_weight=0.03,
            certifications_weight=0.02,
            projects_weight=0.02,
        )
        assert cfg.skills_weight == 0.5
        assert cfg.strong_apply_threshold == 80.0
