from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.resume_optimization.ats import ATSScorer
from app.resume_optimization.cache import OptimizationCache
from app.resume_optimization.config import OptimizationConfig
from app.resume_optimization.exceptions import ResumeOptimizationValidationError
from app.resume_optimization.keyword_extractor import KeywordExtractor
from app.resume_optimization.optimizer import ResumeOptimizer
from app.resume_optimization.schemas import (
    ATSAssessment,
    ChangeLogEntry,
    ChangeType,
    KeywordAnalysis,
    OptimizationSummary,
    OptimizedResume,
    OptimizedSection,
)
from app.resume_optimization.section_optimizer import SectionOptimizer
from app.resume_optimization.service import ResumeOptimizationService
from app.resume_optimization.validator import ResumeValidator


@pytest.fixture
def config() -> OptimizationConfig:
    return OptimizationConfig()


@pytest.fixture
def service(config: OptimizationConfig) -> ResumeOptimizationService:
    return ResumeOptimizationService(config=config)


def make_resume(
    summary=None,
    skills=None,
    experience_bullets=None,
    projects=None,
    education=None,
    certifications=None,
):
    resume = MagicMock()
    resume.sections = []
    resume.content = {}

    if summary:
        sec = MagicMock()
        sec.section_type = "professional_summary"
        sec.title = "Professional Summary"
        sec.content = summary
        resume.sections.append(sec)

    if skills is not None:
        sec = MagicMock()
        sec.section_type = "skills"
        sec.title = "Skills"
        sec.content = {"skills": skills}
        resume.sections.append(sec)

    if experience_bullets:
        for i, bullets in enumerate(experience_bullets):
            sec = MagicMock()
            sec.section_type = "experience"
            sec.title = f"Experience {i}"
            sec.content = "\n".join(bullets) if isinstance(bullets, list) else bullets
            resume.sections.append(sec)

    if projects:
        for proj in projects:
            sec = MagicMock()
            sec.section_type = "projects"
            sec.title = proj.get("title", "Project")
            sec.content = proj.get("description", "")
            resume.sections.append(sec)

    if education:
        for edu in education:
            sec = MagicMock()
            sec.section_type = "education"
            sec.title = edu.get("degree", "Degree")
            sec.content = edu.get("description", "")
            resume.sections.append(sec)

    if certifications:
        for cert in certifications:
            sec = MagicMock()
            sec.section_type = "certifications"
            sec.title = cert
            sec.content = cert
            resume.sections.append(sec)

    return resume


def make_job_posting(
    skills=None,
    title="Software Engineer",
    description=None,
    company_industry="Tech",
):
    job = MagicMock()
    job.id = uuid.uuid4()
    job.title = title
    job.skills = skills or []
    job.description = description

    company = MagicMock()
    company.name = "Acme"
    company.industry = company_industry
    job.company = company

    sal = MagicMock()
    sal.min_amount = 100000
    sal.max_amount = 150000
    job.salary = sal

    loc = MagicMock()
    loc.city = "New York"
    loc.state = "NY"
    loc.country = "US"
    loc.remote_type = "remote"
    loc.display_name = "New York, NY"
    job.location = loc

    job.employment_type = "full_time"
    job.experience_level = "mid"
    return job


def make_profile(hash_val=None):
    profile = MagicMock()
    profile.profile_hash = hash_val or "profile123"
    profile.personal_summary = "Experienced software engineer with 5 years of experience."
    return profile


def make_match_result(matching=None, preferred=None):
    result = MagicMock()
    result.matching_skills = []
    for s in (matching or []):
        ms = MagicMock()
        ms.name = s
        ms.matched = True
        result.matching_skills.append(ms)
    result.preferred_skills = []
    for s in (preferred or []):
        ps = MagicMock()
        ps.name = s
        ps.matched = False
        result.preferred_skills.append(ps)
    return result


class TestKeywordExtractor:
    def test_extract_required_skills(self):
        extractor = KeywordExtractor()
        job = make_job_posting(skills=["Python", "SQL", "Docker"])
        result = extractor.extract(job, None)
        assert "Python" in result.required_keywords or "Python" in result.technical_skills
        assert len(result.required_keywords) + len(result.technical_skills) >= 2

    def test_extract_with_match_result(self):
        extractor = KeywordExtractor()
        job = make_job_posting(skills=["Python"])
        match = make_match_result(matching=["Python"], preferred=["Docker"])
        result = extractor.extract(job, match)
        assert "Python" in result.required_keywords or "Python" in result.technical_skills

    def test_extract_industry_terms(self):
        extractor = KeywordExtractor()
        job = make_job_posting(
            skills=["Python"],
            description="We are a fintech SaaS company using machine learning and agile methodologies.",
        )
        result = extractor.extract(job, None)
        assert any("Fintech" in t for t in result.industry_terms)
        assert any("SaaS" in t or "Saas" in t for t in result.industry_terms)

    def test_extract_soft_skills(self):
        extractor = KeywordExtractor()
        job = make_job_posting(
            skills=["Python"],
            description="We need strong leadership and communication skills.",
        )
        result = extractor.extract(job, None)
        assert any("Leadership" in s for s in result.soft_skills)
        assert any("Communication" in s for s in result.soft_skills)

    def test_extract_empty_job(self):
        extractor = KeywordExtractor()
        result = extractor.extract(None, None)
        assert result.required_keywords == []
        assert result.keyword_density == 0.0

    def test_classify_tech(self):
        assert KeywordExtractor._classify_tech("python") == "programming_languages"
        assert KeywordExtractor._classify_tech("react") == "frameworks"
        assert KeywordExtractor._classify_tech("postgresql") == "databases"
        assert KeywordExtractor._classify_tech("aws") == "cloud_platforms"
        assert KeywordExtractor._classify_tech("git") == "tools"

    def test_keyword_density(self):
        density = KeywordExtractor._compute_keyword_density(
            "Python SQL Docker Python", ["Python", "SQL"]
        )
        assert density > 0.0

    def test_missing_required(self):
        extractor = KeywordExtractor()
        job = make_job_posting(skills=["Python", "Kubernetes", "AWS"])
        result = extractor.extract(job, None)
        assert result.missing_required is not None


class TestSectionOptimizer:
    def test_optimize_summary_adds_keywords(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        keywords = KeywordAnalysis(
            required_keywords=["Python", "Docker", "Kubernetes"],
        )
        optimized, log = optimizer.optimize_summary(
            "Experienced engineer.", None, keywords,
        )
        assert optimized is not None
        assert "Python" in optimized or "Docker" in optimized
        assert log is not None
        assert log.change_type == ChangeType.REWRITTEN

    def test_optimize_summary_no_change(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        keywords = KeywordAnalysis()
        optimized, log = optimizer.optimize_summary(
            "Experienced engineer.", None, keywords,
        )
        assert "Experienced engineer." in (optimized or "")
        assert log.change_type == ChangeType.UNCHANGED

    def test_optimize_summary_both_none(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        result, log = optimizer.optimize_summary(None, None, KeywordAnalysis())
        assert result is None
        assert log is None

    def test_optimize_skills_reorders_by_relevance(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        keywords = KeywordAnalysis(
            required_keywords=["Python"],
            technical_skills=["Docker"],
            preferred_keywords=["SQL"],
        )
        optimized, log = optimizer.optimize_skills(
            ["CSS", "HTML", "Python", "SQL"], keywords,
        )
        assert optimized.index("Python") < optimized.index("CSS")
        assert log.change_type == ChangeType.REORDERED

    def test_optimize_skills_empty(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        result, log = optimizer.optimize_skills(None, KeywordAnalysis())
        assert result == []

    def test_optimize_skills_adds_missing(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        keywords = KeywordAnalysis(
            required_keywords=["Python", "Kubernetes"],
        )
        optimized, log = optimizer.optimize_skills(
            ["CSS"], keywords,
        )
        assert "Python" in optimized

    def test_optimize_experience_bullets(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        keywords = KeywordAnalysis(
            required_keywords=["Python", "Docker"],
        )
        section = OptimizedSection(
            section_type="experience",
            title="Engineer at Acme",
            original_content="Built web applications.\nLed team of 5.",
        )
        result, log = optimizer.optimize_experience_bullets(section, keywords)
        assert result.optimized_content is not None
        assert "python" in result.optimized_content.lower() or "docker" in result.optimized_content.lower()

    def test_optimize_experience_bullets_no_change(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        section = OptimizedSection(
            section_type="experience",
            title="Engineer at Acme",
            original_content="Built web applications.",
        )
        result, log = optimizer.optimize_experience_bullets(section, KeywordAnalysis())
        assert result.change_type == ChangeType.UNCHANGED

    def test_optimize_projects_reorders(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        keywords = KeywordAnalysis(required_keywords=["Python"])
        sections = [
            OptimizedSection(section_type="projects", title="CSS Project",
                             original_content="Built with CSS"),
            OptimizedSection(section_type="projects", title="Python Project",
                             original_content="Built with Python"),
        ]
        result, logs = optimizer.optimize_projects(sections, keywords)
        assert result[0].title == "Python Project"

    def test_optimize_projects_empty(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        result, logs = optimizer.optimize_projects([], KeywordAnalysis())
        assert result == []
        assert logs == []

    def test_optimize_education_reorders(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        keywords = KeywordAnalysis(required_keywords=["Computer Science"])
        sections = [
            OptimizedSection(section_type="education", title="BA in English",
                             original_content="English literature"),
            OptimizedSection(section_type="education", title="BS in Computer Science",
                             original_content="Computer science degree"),
        ]
        result, logs = optimizer.optimize_education(sections, keywords)
        assert result[0].title == "BS in Computer Science"

    def test_optimize_certifications_unchanged(self):
        optimizer = SectionOptimizer(KeywordExtractor())
        sections = [OptimizedSection(section_type="certifications", title="AWS")]
        result, logs = optimizer.optimize_certifications(sections, KeywordAnalysis())
        assert len(result) == 1
        assert logs == []


class TestATSScorer:
    def test_assess_perfect(self):
        scorer = ATSScorer()
        keywords = KeywordAnalysis(
            required_keywords=["Python"],
            preferred_keywords=["SQL"],
            technical_skills=["Docker"],
        )
        result = scorer.assess(
            keywords=keywords,
            has_summary=True,
            has_skills_section=True,
            has_experience_section=True,
            has_education_section=True,
            has_projects_section=True,
            has_certifications_section=True,
            skill_count=15,
            summary_text="Python SQL Docker expert",
            experience_text="Built with Python and Docker",
        )
        assert result.overall_score >= 60
        assert 0 <= result.overall_score <= 100

    def test_assess_poor(self):
        scorer = ATSScorer()
        keywords = KeywordAnalysis(
            required_keywords=["Python", "Kubernetes", "AWS"],
            missing_required=["Python", "Kubernetes", "AWS"],
        )
        result = scorer.assess(
            keywords=keywords,
            has_summary=False,
            has_skills_section=False,
            has_experience_section=False,
            has_education_section=False,
            has_projects_section=False,
            has_certifications_section=False,
            skill_count=0,
            summary_text=None,
            experience_text=None,
        )
        assert result.overall_score <= 50

    def test_assess_generates_suggestions(self):
        scorer = ATSScorer()
        keywords = KeywordAnalysis(
            required_keywords=["Python"],
            missing_required=["Python"],
        )
        result = scorer.assess(
            keywords=keywords,
            has_summary=False,
            has_skills_section=False,
            has_experience_section=False,
            has_education_section=False,
            has_projects_section=False,
            has_certifications_section=False,
            skill_count=0,
            summary_text=None,
            experience_text=None,
        )
        assert len(result.suggestions) > 0

    def test_score_keyword_match_all_missing(self):
        score = ATSScorer._score_keyword_match(
            KeywordAnalysis(required_keywords=["A"], missing_required=["A"])
        )
        assert score == 0

    def test_score_keyword_match_no_keywords(self):
        score = ATSScorer._score_keyword_match(KeywordAnalysis())
        assert score == 50

    def test_score_section_coverage_all(self):
        score = ATSScorer._score_section_coverage(True, True, True, True, True, True)
        assert score == 100

    def test_score_section_coverage_none(self):
        score = ATSScorer._score_section_coverage(False, False, False, False, False, False)
        assert score == 0


class TestResumeValidator:
    def test_validate_empty_resume(self):
        validator = ResumeValidator(OptimizationConfig())
        warnings = validator.validate_resume(None)
        assert len(warnings) > 0

    def test_validate_no_content(self):
        validator = ResumeValidator(OptimizationConfig())
        resume = MagicMock()
        resume.sections = []
        resume.content = None
        resume.description = None
        warnings = validator.validate_resume(resume)
        assert any("content" in w.lower() for w in warnings)

    def test_validate_valid_resume(self):
        validator = ResumeValidator(OptimizationConfig())
        resume = make_resume(summary="Test", skills=["Python"])
        warnings = validator.validate_resume(resume)
        assert len(warnings) == 0

    def test_validate_job_empty(self):
        validator = ResumeValidator(OptimizationConfig())
        warnings = validator.validate_job(None)
        assert len(warnings) > 0

    def test_validate_job_no_skills(self):
        validator = ResumeValidator(OptimizationConfig())
        job = make_job_posting(skills=[])
        warnings = validator.validate_job(job)
        assert any("skills" in w.lower() for w in warnings)

    def test_validate_job_valid(self):
        validator = ResumeValidator(OptimizationConfig())
        job = make_job_posting(skills=["Python"])
        warnings = validator.validate_job(job)
        assert len(warnings) == 0

    def test_assert_valid_input_raises(self):
        validator = ResumeValidator(OptimizationConfig())
        with pytest.raises(ResumeOptimizationValidationError):
            validator.assert_valid_input(None, None, None)

    def test_assert_valid_input_ok(self):
        validator = ResumeValidator(OptimizationConfig())
        resume = make_resume(summary="Test", skills=["Python"])
        job = make_job_posting(skills=["Python"])
        profile = make_profile()
        validator.assert_valid_input(resume, job, profile)

    def test_strict_validation_finds_duplicates(self):
        config = OptimizationConfig(validation_strictness="strict")
        validator = ResumeValidator(config)
        sec1 = MagicMock()
        sec1.section_type = "skills"
        sec1.content = {"skills": ["Python", "Python", "SQL"]}
        resume = MagicMock()
        resume.sections = [sec1]
        resume.content = None
        resume.description = None
        warnings = validator.validate_resume(resume)
        assert any("duplicate" in w.lower() for w in warnings)


class TestOptimizationCache:
    def test_set_and_get(self):
        cache = OptimizationCache(OptimizationConfig(cache_ttl_seconds=60))
        result = OptimizedResume()
        cache.set("test", result)
        cached = cache.get("test")
        assert cached is not None
        assert cached.id == result.id

    def test_miss(self):
        cache = OptimizationCache(OptimizationConfig(cache_ttl_seconds=60))
        assert cache.get("nonexistent") is None

    def test_invalidate(self):
        cache = OptimizationCache(OptimizationConfig(cache_ttl_seconds=60))
        cache.set("test", OptimizedResume())
        cache.invalidate("test")
        assert cache.get("test") is None

    def test_clear(self):
        cache = OptimizationCache(OptimizationConfig(cache_ttl_seconds=60))
        cache.set("a", OptimizedResume())
        cache.set("b", OptimizedResume())
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_ttl_expiry(self):
        cache = OptimizationCache(OptimizationConfig(cache_ttl_seconds=0))
        cache.set("test", OptimizedResume())
        assert cache.get("test") is None

    def test_compute_key(self):
        cache = OptimizationCache(OptimizationConfig())
        key = cache.compute_key("p123", "j456", "r789")
        assert "p123" in key
        assert "j456" in key


class TestResumeOptimizer:
    def test_optimize_full(self):
        config = OptimizationConfig()
        extractor = KeywordExtractor()
        section_optimizer = SectionOptimizer(extractor)
        ats_scorer = ATSScorer()
        optimizer = ResumeOptimizer(config, extractor, section_optimizer, ats_scorer)

        resume = make_resume(
            summary="Experienced software engineer.",
            skills=["Python", "CSS", "HTML", "SQL"],
            experience_bullets=[
                ["Built web applications.", "Led team of 5 developers."],
            ],
            projects=[
                {"title": "Web App", "description": "Built with Python"},
                {"title": "Mobile App", "description": "Built with Swift"},
            ],
            education=[
                {"degree": "BS in Computer Science", "description": "CS degree"},
            ],
            certifications=["AWS Certified Developer"],
        )
        job = make_job_posting(
            skills=["Python", "SQL", "Docker", "Kubernetes"],
            title="Senior Python Developer",
            description="We build fintech solutions with machine learning.",
        )
        profile = make_profile()
        match = make_match_result(matching=["Python", "SQL"], preferred=["FastAPI"])

        result = optimizer.optimize(resume, job, profile, match)
        assert result.professional_summary is not None
        assert len(result.skills) > 0
        assert len(result.experience_sections) > 0
        assert len(result.project_sections) > 0
        assert len(result.education_sections) > 0
        assert len(result.certification_sections) > 0
        assert result.ats_assessment.overall_score >= 0
        assert result.optimization_summary.original_ats_score >= 0
        assert len(result.change_log) > 0

    def test_optimize_minimal(self):
        config = OptimizationConfig()
        extractor = KeywordExtractor()
        section_optimizer = SectionOptimizer(extractor)
        ats_scorer = ATSScorer()
        optimizer = ResumeOptimizer(config, extractor, section_optimizer, ats_scorer)

        result = optimizer.optimize(None, None, None, None)
        assert result.professional_summary is None
        assert result.skills == []
        assert result.ats_assessment.overall_score >= 0

    def test_optimize_empty_resume(self):
        config = OptimizationConfig()
        extractor = KeywordExtractor()
        section_optimizer = SectionOptimizer(extractor)
        ats_scorer = ATSScorer()
        optimizer = ResumeOptimizer(config, extractor, section_optimizer, ats_scorer)

        resume = make_resume()
        job = make_job_posting(skills=["Python"])
        profile = make_profile()
        result = optimizer.optimize(resume, job, profile, None)
        assert result is not None
        assert result.ats_assessment is not None


class TestResumeOptimizationService:
    def test_optimize_full(self, service):
        resume = make_resume(
            summary="Experienced software engineer.",
            skills=["Python", "SQL", "CSS"],
            experience_bullets=[
                ["Built web applications.", "Led team."],
            ],
        )
        job = make_job_posting(
            skills=["Python", "SQL", "Docker"],
            description="Fintech company seeking Python engineers.",
        )
        profile = make_profile()
        match = make_match_result(matching=["Python"])
        result = service.optimize(resume, job, profile, match)
        assert result is not None
        assert result.ats_assessment is not None
        assert result.professional_summary is not None

    def test_optimize_invalid_resume(self, service):
        with pytest.raises(ResumeOptimizationValidationError):
            service.optimize(None, None, None, None)

    def test_optimize_caching(self, service):
        resume = make_resume(summary="Test", skills=["Python"])
        job = make_job_posting(skills=["Python"])
        profile = make_profile()
        match = make_match_result(matching=["Python"])
        result1 = service.optimize(resume, job, profile, match)
        result2 = service.optimize(resume, job, profile, match)
        assert result1.id == result2.id

    def test_optimize_skip_cache(self, service):
        resume = make_resume(summary="Test", skills=["Python"])
        job = make_job_posting(skills=["Python"])
        profile = make_profile()
        match = make_match_result(matching=["Python"])
        result1 = service.optimize(resume, job, profile, match, skip_cache=True)
        result2 = service.optimize(resume, job, profile, match, skip_cache=False)
        assert result1.id == result2.id

    def test_invalidate_cache(self, service):
        resume = make_resume(summary="Test", skills=["Python"])
        job = make_job_posting(skills=["Python"])
        profile = make_profile()
        match = make_match_result(matching=["Python"])
        service.optimize(resume, job, profile, match)
        service.clear_cache()
        result2 = service.optimize(resume, job, profile, match)
        assert result2 is not None

    def test_clear_cache(self, service):
        resume = make_resume(summary="Test", skills=["Python"])
        job = make_job_posting(skills=["Python"])
        profile = make_profile()
        match = make_match_result(matching=["Python"])
        service.optimize(resume, job, profile, match)
        service.clear_cache()
        assert service._cache.get("anything") is None

    def test_deterministic_output(self, service):
        resume = make_resume(
            summary="Engineer.",
            skills=["Python", "SQL"],
            experience_bullets=[["Built apps."]],
        )
        job = make_job_posting(skills=["Python", "SQL"])
        profile = make_profile()
        match = make_match_result(matching=["Python", "SQL"])
        result1 = service.optimize(resume, job, profile, match)
        result2 = service.optimize(resume, job, profile, match)
        assert result1.ats_assessment.overall_score == result2.ats_assessment.overall_score


class TestSchemas:
    def test_optimized_resume_defaults(self):
        result = OptimizedResume()
        assert result.skills == []
        assert result.experience_sections == []
        assert result.ats_assessment.overall_score == 0
        assert result.optimization_summary.original_ats_score == 0

    def test_keyword_analysis_defaults(self):
        ka = KeywordAnalysis()
        assert ka.required_keywords == []
        assert ka.keyword_density == 0.0

    def test_ats_assessment_defaults(self):
        assessment = ATSAssessment()
        assert assessment.overall_score == 0
        assert assessment.suggestions == []

    def test_change_log_entry_defaults(self):
        log = ChangeLogEntry(section="test")
        assert log.change_type == ChangeType.UNCHANGED
        assert log.description is None

    def test_optimization_summary_defaults(self):
        summary = OptimizationSummary()
        assert summary.original_ats_score == 0
        assert summary.sections_optimized == 0

    def test_optimized_section_defaults(self):
        section = OptimizedSection(section_type="experience")
        assert section.title is None
        assert section.change_type == ChangeType.UNCHANGED
        assert section.keywords_added == []


class TestConfig:
    def test_default_config(self):
        cfg = OptimizationConfig()
        assert cfg.optimization_level == "balanced"
        assert cfg.ats_keyword_density_target == 0.02

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError):
            OptimizationConfig(optimization_level="invalid")

    def test_invalid_strictness_raises(self):
        with pytest.raises(ValueError):
            OptimizationConfig(validation_strictness="invalid")

    def test_invalid_density_raises(self):
        with pytest.raises(ValueError):
            OptimizationConfig(ats_keyword_density_target=1.5)

    def test_invalid_intensity_raises(self):
        with pytest.raises(ValueError):
            OptimizationConfig(max_rewrite_intensity=-0.1)

    def test_custom_config(self):
        cfg = OptimizationConfig(
            optimization_level="aggressive",
            cache_ttl_seconds=600,
            max_skills_to_include=30,
        )
        assert cfg.optimization_level == "aggressive"
        assert cfg.cache_ttl_seconds == 600
