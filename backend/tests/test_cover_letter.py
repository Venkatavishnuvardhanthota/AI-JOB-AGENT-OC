from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.cover_letter.cache import CoverLetterCache
from app.cover_letter.config import CoverLetterConfig
from app.cover_letter.exceptions import CoverLetterValidationError
from app.cover_letter.generator import CoverLetterGenerator
from app.cover_letter.personalizer import Personalizer
from app.cover_letter.schemas import (
    CoverLetterSection,
    GeneratedCoverLetter,
    PersonalizationData,
)
from app.cover_letter.service import CoverLetterGenerationService
from app.cover_letter.templates import COVER_LETTER_TEMPLATES, TemplateEngine
from app.cover_letter.validator import CoverLetterValidator


@pytest.fixture
def config() -> CoverLetterConfig:
    return CoverLetterConfig()


@pytest.fixture
def service(config: CoverLetterConfig) -> CoverLetterGenerationService:
    return CoverLetterGenerationService(config=config)


def make_profile(hash_val="profile123"):
    profile = MagicMock()
    profile.profile_hash = hash_val
    profile.current_role = "Senior Software Engineer"
    profile.years_of_experience = 5.0
    profile.career_level = "senior"
    profile.primary_skills = ["Python", "SQL", "FastAPI", "Docker", "Kubernetes"]
    profile.secondary_skills = ["React", "TypeScript"]
    profile.strengths = [
        "Led migration of monolith to microservices, improving deployment frequency by 3x",
        "Designed and implemented real-time data pipeline processing 1M+ events/day",
    ]
    profile.personal_summary = "Experienced senior software engineer with expertise in backend systems."
    profile.career_goals = "Seeking a challenging engineering leadership role."
    profile.education_summary = "MS in Computer Science from Stanford University"
    profile.certifications = ["AWS Certified Solutions Architect", "Kubernetes Administrator"]
    profile.industries = ["Fintech", "SaaS"]
    profile.preferred_locations = ["San Francisco", "New York"]
    profile.employment_preference = "Full Time"
    profile.salary_expectation = "USD 180,000/year"
    return profile


def make_job_posting(
    title="Senior Backend Engineer",
    company_name="TechCorp",
    industry="Fintech",
    skills=None,
):
    job = MagicMock()
    job.id = uuid.uuid4()
    job.title = title
    job.skills = skills or ["Python", "SQL", "FastAPI", "Docker", "Kubernetes", "AWS"]
    job.description = "We are a fintech company building the future of payments."
    company = MagicMock()
    company.name = company_name
    company.industry = industry
    job.company = company
    job.employment_type = "full_time"
    job.experience_level = "senior"
    return job


def make_optimized_resume(hash_val="resume123"):
    resume = MagicMock()
    resume.resume_hash = hash_val
    resume.professional_summary = "Experienced senior software engineer."
    resume.skills = ["Python", "SQL", "FastAPI", "Docker", "Kubernetes"]
    resume.project_sections = []
    proj = MagicMock()
    proj.title = "Payment Processing System"
    proj.section_type = "projects"
    resume.project_sections.append(proj)
    proj2 = MagicMock()
    proj2.title = "Real-time Analytics Dashboard"
    proj2.section_type = "projects"
    resume.project_sections.append(proj2)
    return resume


def make_match_result():
    result = MagicMock()
    result.matching_skills = []
    for s in ["Python", "SQL", "FastAPI", "Docker"]:
        ms = MagicMock()
        ms.name = s
        ms.matched = True
        result.matching_skills.append(ms)
    return result


class TestTemplateEngine:
    def test_get_template_existing(self):
        engine = TemplateEngine()
        template = engine.get_template("software_engineer")
        assert "opening" in template
        assert "closing" in template

    def test_get_template_missing_falls_back(self):
        engine = TemplateEngine()
        template = engine.get_template("nonexistent")
        assert template == COVER_LETTER_TEMPLATES["general"]

    def test_list_styles(self):
        engine = TemplateEngine()
        styles = engine.list_styles()
        assert "general" in styles
        assert "software_engineer" in styles

    def test_render_replaces_variables(self):
        engine = TemplateEngine()
        result = engine.render("Hello {name}!", {"name": "World"})
        assert result == "Hello World!"

    def test_render_missing_variable(self):
        engine = TemplateEngine()
        result = engine.render("Hello {name}!", {})
        assert "{name}" in result

    def test_get_sections_for_length_short(self):
        engine = TemplateEngine()
        sections = engine.get_sections_for_length("short")
        assert "projects" not in sections
        assert "company" not in sections
        assert "greeting" in sections
        assert "opening" in sections
        assert "experience" in sections
        assert "skills" in sections
        assert "closing" in sections

    def test_get_sections_for_length_long(self):
        engine = TemplateEngine()
        sections = engine.get_sections_for_length("long")
        assert "projects" in sections
        assert "company" in sections


class TestPersonalizer:
    def test_extract_full(self):
        personalizer = Personalizer()
        profile = make_profile()
        job = make_job_posting()
        resume = make_optimized_resume()
        match = make_match_result()
        data = personalizer.extract(profile, job, match, resume)
        assert data.company_name == "TechCorp"
        assert data.job_title == "Senior Backend Engineer"
        assert data.current_role == "Senior Software Engineer"
        assert data.years_experience == 5.0
        assert len(data.primary_skills) > 0
        assert len(data.matching_skills) > 0
        assert len(data.strengths) > 0
        assert len(data.projects) > 0

    def test_extract_minimal(self):
        personalizer = Personalizer()
        data = personalizer.extract(None, None, None, None)
        assert data.company_name is None
        assert data.job_title is None
        assert data.primary_skills == []

    def test_build_variables(self):
        personalizer = Personalizer()
        data = PersonalizationData(
            company_name="Acme",
            job_title="Engineer",
            current_role="Senior Engineer",
            years_experience=5.0,
            career_level="senior",
            primary_skills=["Python", "SQL"],
            matching_skills=["Python"],
            strengths=["Led major project"],
            projects=["Project A"],
        )
        vars = personalizer.build_variables(data, "professional", "general")
        assert vars["company_name"] == "Acme"
        assert vars["job_title"] == "Engineer"
        assert vars["years_experience"] == "5"
        assert vars["matching_skills_count"] == "1"

    def test_build_variables_empty(self):
        personalizer = Personalizer()
        data = PersonalizationData()
        vars = personalizer.build_variables(data, "professional", "general")
        assert vars["company_name"] == "your company"
        assert vars["years_experience"] == "several"


class TestCoverLetterGenerator:
    def test_generate_full(self):
        config = CoverLetterConfig(length="long")
        generator = CoverLetterGenerator(
            config,
            TemplateEngine(),
            Personalizer(),
            CoverLetterValidator(config),
        )
        profile = make_profile()
        job = make_job_posting()
        resume = make_optimized_resume()
        match = make_match_result()
        result = generator.generate(profile, job, resume, match)
        assert result.full_text is not None
        assert result.greeting is not None
        assert result.opening_paragraph is not None
        assert result.experience_paragraph is not None
        assert result.skills_paragraph is not None
        assert result.closing_paragraph is not None
        assert result.signature is not None
        assert len(result.sections) > 0
        assert result.word_count > 0

    def test_generate_short(self):
        config = CoverLetterConfig(length="short")
        generator = CoverLetterGenerator(
            config,
            TemplateEngine(),
            Personalizer(),
            CoverLetterValidator(config),
        )
        result = generator.generate(make_profile(), make_job_posting(), make_optimized_resume(), make_match_result())
        assert result.full_text is not None
        assert result.company_paragraph is None
        assert result.projects_paragraph is None

    def test_generate_infers_style(self):
        config = CoverLetterConfig(length="medium")
        generator = CoverLetterGenerator(
            config,
            TemplateEngine(),
            Personalizer(),
            CoverLetterValidator(config),
        )
        job = make_job_posting(title="Software Engineer")
        result = generator.generate(make_profile(), job, make_optimized_resume(), make_match_result())
        assert result.full_text is not None

    def test_generate_minimal_inputs(self):
        config = CoverLetterConfig(length="short")
        generator = CoverLetterGenerator(
            config,
            TemplateEngine(),
            Personalizer(),
            CoverLetterValidator(config),
        )
        result = generator.generate(None, None, None, None)
        assert result.full_text is not None
        assert result.warnings is not None

    def test_template_with_company_name(self):
        config = CoverLetterConfig()
        generator = CoverLetterGenerator(
            config,
            TemplateEngine(),
            Personalizer(),
            CoverLetterValidator(config),
        )
        job = make_job_posting(company_name="Google")
        result = generator.generate(make_profile(), job, make_optimized_resume(), make_match_result())
        assert "Google" in (result.full_text or "")

    def test_template_with_job_title(self):
        config = CoverLetterConfig()
        generator = CoverLetterGenerator(
            config,
            TemplateEngine(),
            Personalizer(),
            CoverLetterValidator(config),
        )
        job = make_job_posting(title="Data Scientist")
        result = generator.generate(make_profile(), job, make_optimized_resume(), make_match_result())
        assert "Data Scientist" in (result.full_text or "")


class TestCoverLetterValidator:
    def test_validate_inputs_missing_all(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        warnings = validator.validate_inputs(None, None, None)
        assert len(warnings) > 0

    def test_validate_inputs_valid(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        profile = make_profile()
        job = make_job_posting()
        resume = make_optimized_resume()
        warnings = validator.validate_inputs(profile, job, resume)
        assert len(warnings) == 0

    def test_validate_inputs_missing_company_name(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        job = MagicMock()
        job.title = "Engineer"
        job.company = None
        warnings = validator.validate_inputs(make_profile(), job, make_optimized_resume())
        assert any("company" in w.lower() for w in warnings)

    def test_assert_valid_inputs_raises(self):
        validator = CoverLetterValidator(CoverLetterConfig(strict_validation=True))
        with pytest.raises(CoverLetterValidationError):
            validator.assert_valid_inputs(None, None, None)

    def test_assert_valid_inputs_ok(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        validator.assert_valid_inputs(make_profile(), make_job_posting(), make_optimized_resume())

    def test_validate_output_empty(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        cl = GeneratedCoverLetter()
        warnings = validator.validate_output(cl)
        assert any("empty" in w.lower() for w in warnings)

    def test_validate_output_valid(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        cl = GeneratedCoverLetter(full_text="Dear Hiring Manager,\n\nI am writing to apply...")
        warnings = validator.validate_output(cl)
        assert len(warnings) == 0

    def test_validate_output_too_long(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        long_text = "word " * 600
        cl = GeneratedCoverLetter(full_text=long_text)
        warnings = validator.validate_output(cl)
        assert any("length" in w.lower() for w in warnings)

    def test_check_unsupported_claims(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        text = "I single-handedly built the best platform in the industry."
        warnings = validator._check_unsupported_claims(text)
        assert len(warnings) > 0

    def test_check_unsupported_claims_clean(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        text = "I contributed to the development of several features."
        warnings = validator._check_unsupported_claims(text)
        assert len(warnings) == 0

    def test_validate_sections_duplicate(self):
        validator = CoverLetterValidator(CoverLetterConfig())
        sections = [
            {"section_type": "opening", "content": "Same text"},
            {"section_type": "closing", "content": "Same text"},
        ]
        warnings = validator.validate_sections(sections)
        assert any("duplicate" in w.lower() for w in warnings)


class TestCoverLetterCache:
    def test_set_and_get(self):
        cache = CoverLetterCache(CoverLetterConfig(cache_ttl_seconds=60))
        result = GeneratedCoverLetter()
        cache.set("test", result)
        cached = cache.get("test")
        assert cached is not None
        assert cached.id == result.id

    def test_miss(self):
        cache = CoverLetterCache(CoverLetterConfig(cache_ttl_seconds=60))
        assert cache.get("nonexistent") is None

    def test_invalidate(self):
        cache = CoverLetterCache(CoverLetterConfig(cache_ttl_seconds=60))
        cache.set("test", GeneratedCoverLetter())
        cache.invalidate("test")
        assert cache.get("test") is None

    def test_clear(self):
        cache = CoverLetterCache(CoverLetterConfig(cache_ttl_seconds=60))
        cache.set("a", GeneratedCoverLetter())
        cache.set("b", GeneratedCoverLetter())
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_ttl_expiry(self):
        cache = CoverLetterCache(CoverLetterConfig(cache_ttl_seconds=0))
        cache.set("test", GeneratedCoverLetter())
        assert cache.get("test") is None

    def test_compute_key(self):
        cache = CoverLetterCache(CoverLetterConfig())
        key = cache.compute_key("p123", "j456", "r789", "general", "professional")
        assert "p123" in key
        assert "j456" in key
        assert "general" in key


class TestCoverLetterGenerationService:
    def test_generate_full(self, service):
        result = service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
        )
        assert result.full_text is not None
        assert result.word_count > 0
        assert len(result.sections) > 0

    def test_generate_with_custom_tone(self, service):
        result = service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
            tone="enthusiastic",
        )
        assert result.full_text is not None
        assert result.configuration.get("tone") == "enthusiastic"

    def test_generate_with_custom_length(self, service):
        result = service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
            length="short",
        )
        assert result.full_text is not None
        assert result.projects_paragraph is None

    def test_generate_invalid_inputs(self, service):
        with pytest.raises(CoverLetterValidationError):
            service.generate(profile=None, job_posting=None, optimized_resume=None, match_result=None)

    def test_caching(self, service):
        result1 = service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
        )
        result2 = service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
        )
        assert result1.id == result2.id

    def test_skip_cache(self, service):
        result1 = service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
            skip_cache=True,
        )
        result2 = service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
            skip_cache=False,
        )
        assert result1.id == result2.id

    def test_clear_cache(self, service):
        service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
        )
        service.clear_cache()
        result2 = service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
        )
        assert result2 is not None

    def test_invalidate_cache(self, service):
        service.generate(
            make_profile(),
            make_job_posting(),
            make_optimized_resume(),
            make_match_result(),
        )
        service.clear_cache()
        assert service._cache.get("anything") is None

    def test_deterministic_output(self, service):
        profile = make_profile()
        job = make_job_posting()
        resume = make_optimized_resume()
        match = make_match_result()
        result1 = service.generate(profile, job, resume, match)
        result2 = service.generate(profile, job, resume, match)
        assert result1.full_text == result2.full_text

    def test_list_templates(self, service):
        templates = service.list_templates()
        assert "general" in templates
        assert len(templates) >= 3


class TestSchemas:
    def test_generated_cover_letter_defaults(self):
        cl = GeneratedCoverLetter()
        assert cl.sections == []
        assert cl.word_count == 0
        assert cl.warnings == []

    def test_personalization_data_defaults(self):
        data = PersonalizationData()
        assert data.primary_skills == []
        assert data.company_name is None

    def test_cover_letter_section_defaults(self):
        section = CoverLetterSection(section_type="opening", content="Hello")
        assert section.section_type == "opening"
        assert section.source_fields == []


class TestConfig:
    def test_default_config(self):
        cfg = CoverLetterConfig()
        assert cfg.tone == "professional"
        assert cfg.length == "medium"

    def test_invalid_tone_raises(self):
        with pytest.raises(ValueError):
            CoverLetterConfig(tone="invalid")

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError):
            CoverLetterConfig(length="invalid")

    def test_invalid_creativity_raises(self):
        with pytest.raises(ValueError):
            CoverLetterConfig(creativity=1.5)

    def test_custom_config(self):
        cfg = CoverLetterConfig(
            tone="enthusiastic",
            length="short",
            cache_ttl_seconds=600,
            strict_validation=False,
        )
        assert cfg.tone == "enthusiastic"
        assert cfg.length == "short"
        assert cfg.strict_validation is False
