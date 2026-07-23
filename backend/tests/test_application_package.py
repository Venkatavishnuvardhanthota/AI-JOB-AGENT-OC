from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from app.application_package.cache import PackageCache
from app.application_package.config import PackageConfig
from app.application_package.generator import PackageGenerator
from app.application_package.schemas import (
    ApplicationPackage,
    PackageStatus,
    PackageValidation,
)
from app.application_package.service import ApplicationPackageService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_job(
    title="Software Engineer",
    company_name="TestCorp",
    skills=None,
):
    company = MagicMock()
    company.name = company_name
    company.website = None
    company.industry = None
    company.size = None

    job = MagicMock()
    job.id = uuid.uuid4()
    job.title = title
    job.company = company
    job.description = "A job description"
    job.skills = skills or ["Python", "Django"]
    return job


def make_mock_profile(profile_hash="prof123"):
    profile = MagicMock()
    profile.profile_hash = profile_hash
    profile.personal_summary = "Experienced developer"
    profile.current_role = "Senior Engineer"
    profile.career_level = "senior"
    profile.years_of_experience = 8
    return profile


def make_mock_ai(profile_hash=None, company_summary="TestCorp"):
    company = MagicMock()
    company.summary = company_summary
    ai = MagicMock()
    ai.profile_hash = profile_hash
    ai.company = company
    return ai


def make_mock_match(job_hash=None, profile_hash=None):
    match = MagicMock()
    match.id = str(uuid.uuid4())
    match.job_hash = job_hash
    match.profile_hash = profile_hash
    match.overall_match_score = 85.0
    return match


def make_mock_resume(resume_hash="resume123", job_hash=None, profile_hash=None):
    resume = MagicMock()
    resume.resume_hash = resume_hash
    resume.job_hash = job_hash
    resume.profile_hash = profile_hash
    return resume


def make_mock_cover_letter(cl_id="cl123"):
    cl = MagicMock()
    cl.id = cl_id
    cl.full_text = "Dear hiring manager..."
    return cl


# ===========================================================================
# Config Tests
# ===========================================================================


class TestPackageConfig:
    def test_default_config(self):
        config = PackageConfig()
        assert config.version == "1.0.0"
        assert config.cache_ttl_seconds == 300
        assert config.strict_validation is True

    def test_weights_sum_to_one(self):
        config = PackageConfig()
        total = (
            config.completeness_weight_job
            + config.completeness_weight_profile
            + config.completeness_weight_ai
            + config.completeness_weight_match
            + config.completeness_weight_resume
            + config.completeness_weight_cover_letter
        )
        assert abs(total - 1.0) < 0.001

    def test_invalid_weights_raises(self):
        try:
            PackageConfig(
                completeness_weight_job=0.5,
                completeness_weight_profile=0.5,
                completeness_weight_ai=0.5,
                completeness_weight_match=0.0,
                completeness_weight_resume=0.0,
                completeness_weight_cover_letter=0.0,
            )
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass


# ===========================================================================
# Cache Tests
# ===========================================================================


class TestPackageCache:
    def test_get_set(self):
        config = PackageConfig()
        cache = PackageCache(config)
        pkg = ApplicationPackage()
        cache.set("key1", pkg)
        cached = cache.get("key1")
        assert cached is not None
        assert cached.id == pkg.id

    def test_get_missing(self):
        cache = PackageCache(PackageConfig())
        assert cache.get("nonexistent") is None

    def test_invalidate(self):
        cache = PackageCache(PackageConfig())
        cache.set("k", ApplicationPackage())
        cache.invalidate("k")
        assert cache.get("k") is None

    def test_clear(self):
        cache = PackageCache(PackageConfig())
        cache.set("a", ApplicationPackage())
        cache.set("b", ApplicationPackage())
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_compute_key(self):
        key = PackageCache.compute_key("p", "j", "r", "c", "m")
        assert "p" in key
        assert "j" in key
        assert "r" in key
        assert "c" in key
        assert "m" in key

    def test_compute_key_with_none(self):
        key = PackageCache.compute_key(None, "j")
        assert key.startswith(":")
        assert "j" in key


# ===========================================================================
# Package Validation (via Generator)
# ===========================================================================


class TestValidation:
    def test_all_inputs_present(self):
        job = make_mock_job()
        profile = make_mock_profile()
        ai = make_mock_ai(profile_hash="prof123")
        match = make_mock_match()
        resume = make_mock_resume()
        cl = make_mock_cover_letter()

        gen = PackageGenerator()
        pkg = gen.generate(job, profile, ai, match, resume, cl)
        assert pkg.validation.all_inputs_present is True
        assert pkg.validation.has_job_posting is True
        assert pkg.validation.has_profile is True
        assert pkg.validation.has_resume is True
        assert pkg.validation.has_cover_letter is True

    def test_only_job(self):
        job = make_mock_job()
        gen = PackageGenerator()
        pkg = gen.generate(job=job)
        assert pkg.validation.all_inputs_present is False
        assert pkg.validation.has_job_posting is True
        assert pkg.validation.has_profile is False
        assert pkg.validation.has_resume is False
        assert pkg.validation.has_cover_letter is False
        assert "Missing optimized resume" in pkg.validation.warnings
        assert "Missing cover letter" in pkg.validation.warnings

    def test_no_inputs(self):
        gen = PackageGenerator()
        pkg = gen.generate()
        assert pkg.validation.all_inputs_present is False
        assert pkg.validation.has_job_posting is False
        assert "Missing job posting" in pkg.warnings

    def test_job_missing_title(self):
        job = make_mock_job(title="")
        gen = PackageGenerator()
        pkg = gen.generate(job=job)
        assert "missing a title" in " ".join(pkg.warnings).lower()

    def test_job_missing_company(self):
        job = make_mock_job()
        job.company = None
        gen = PackageGenerator()
        pkg = gen.generate(job=job)
        assert "missing company" in " ".join(pkg.warnings).lower()

    def test_job_consistency_ok(self):
        job = make_mock_job(company_name="TestCorp")
        ai = make_mock_ai(company_summary="TestCorp")
        gen = PackageGenerator()
        pkg = gen.generate(job=job, application_intelligence=ai)
        assert pkg.validation.job_consistency_ok is True

    def test_job_consistency_mismatch(self):
        job = make_mock_job(company_name="TestCorp")
        ai = make_mock_ai(company_summary="DifferentCorp")
        gen = PackageGenerator()
        pkg = gen.generate(job=job, application_intelligence=ai)
        assert pkg.validation.job_consistency_ok is False
        assert "company name mismatch" in " ".join(pkg.warnings).lower()

    def test_profile_consistency_ok(self):
        profile = make_mock_profile("hash1")
        ai = make_mock_ai(profile_hash="hash1")
        gen = PackageGenerator()
        pkg = gen.generate(profile=profile, application_intelligence=ai)
        assert pkg.validation.profile_consistency_ok is True

    def test_profile_consistency_mismatch(self):
        profile = make_mock_profile("hash1")
        ai = make_mock_ai(profile_hash="hash2")
        gen = PackageGenerator()
        pkg = gen.generate(profile=profile, application_intelligence=ai)
        assert pkg.validation.profile_consistency_ok is False
        assert "profile hash mismatch" in " ".join(pkg.warnings).lower()


# ===========================================================================
# Completeness Tests
# ===========================================================================


class TestCompleteness:
    def test_full_package_complete(self):
        job = make_mock_job()
        profile = make_mock_profile()
        ai = make_mock_ai()
        match = make_mock_match()
        resume = make_mock_resume()
        cl = make_mock_cover_letter()

        gen = PackageGenerator()
        pkg = gen.generate(job, profile, ai, match, resume, cl)
        assert pkg.completeness_score == 100
        assert pkg.status == PackageStatus.COMPLETE

    def test_partial_package(self):
        job = make_mock_job()
        resume = make_mock_resume()
        cover_letter = make_mock_cover_letter()
        gen = PackageGenerator()
        pkg = gen.generate(job=job, resume=resume, cover_letter=cover_letter)
        score = pkg.completeness_score
        assert score >= 50
        assert pkg.status == PackageStatus.PARTIAL

    def test_empty_package(self):
        gen = PackageGenerator()
        pkg = gen.generate()
        assert pkg.completeness_score == 0
        assert pkg.status == PackageStatus.INCOMPLETE

    def test_job_only(self):
        gen = PackageGenerator()
        pkg = gen.generate(job=make_mock_job())
        assert pkg.completeness_score == 15
        assert pkg.status == PackageStatus.INCOMPLETE

    def test_job_and_resume(self):
        gen = PackageGenerator()
        pkg = gen.generate(job=make_mock_job(), resume=make_mock_resume())
        assert pkg.completeness_score == 40
        assert pkg.status == PackageStatus.INCOMPLETE

    def test_job_resume_cover_letter(self):
        gen = PackageGenerator()
        pkg = gen.generate(
            job=make_mock_job(),
            resume=make_mock_resume(),
            cover_letter=make_mock_cover_letter(),
        )
        assert pkg.completeness_score == 65
        assert pkg.status == PackageStatus.PARTIAL


# ===========================================================================
# Generator Tests
# ===========================================================================


class TestGenerator:
    def test_generate_full_package(self):
        job = make_mock_job()
        profile = make_mock_profile()
        ai = make_mock_ai()
        match = make_mock_match()
        resume = make_mock_resume()
        cl = make_mock_cover_letter()

        gen = PackageGenerator()
        pkg = gen.generate(job, profile, ai, match, resume, cl)

        assert isinstance(pkg, ApplicationPackage)
        assert pkg.job is job
        assert pkg.profile is profile
        assert pkg.application_intelligence is ai
        assert pkg.match_result is match
        assert pkg.resume is resume
        assert pkg.cover_letter is cl
        assert pkg.profile_hash == "prof123"
        assert pkg.job_hash is not None
        assert pkg.resume_hash == "resume123"
        assert pkg.cover_letter_hash == "cl123"

    def test_hash_consistency(self):
        job = make_mock_job()
        gen = PackageGenerator()
        pkg1 = gen.generate(job=job)
        pkg2 = gen.generate(job=job)
        assert pkg1.job_hash == pkg2.job_hash

    def test_different_jobs_different_hashes(self):
        job1 = make_mock_job(title="Engineer")
        job2 = make_mock_job(title="Manager")
        gen = PackageGenerator()
        pkg1 = gen.generate(job=job1)
        pkg2 = gen.generate(job=job2)
        assert pkg1.job_hash != pkg2.job_hash

    def test_compute_job_hash_static(self):
        job = make_mock_job()
        h1 = PackageGenerator.compute_job_hash(job)
        h2 = PackageGenerator.compute_job_hash(job)
        assert h1 == h2

    def test_compute_job_hash_none(self):
        assert PackageGenerator.compute_job_hash(None) is None


# ===========================================================================
# Service Tests
# ===========================================================================


class TestService:
    def test_generate_full(self):
        job = make_mock_job()
        profile = make_mock_profile()
        ai = make_mock_ai()
        match = make_mock_match()
        resume = make_mock_resume()
        cl = make_mock_cover_letter()

        service = ApplicationPackageService()
        pkg = service.generate(
            job_posting=job,
            profile_intelligence=profile,
            application_intelligence=ai,
            match_result=match,
            optimized_resume=resume,
            generated_cover_letter=cl,
        )
        assert isinstance(pkg, ApplicationPackage)
        assert pkg.completeness_score == 100

    def test_caching_returns_same(self):
        job = make_mock_job()
        profile = make_mock_profile()
        ai = make_mock_ai()
        match = make_mock_match()
        resume = make_mock_resume()
        cl = make_mock_cover_letter()

        service = ApplicationPackageService()
        pkg1 = service.generate(
            job_posting=job,
            profile_intelligence=profile,
            application_intelligence=ai,
            match_result=match,
            optimized_resume=resume,
            generated_cover_letter=cl,
        )
        pkg2 = service.generate(
            job_posting=job,
            profile_intelligence=profile,
            application_intelligence=ai,
            match_result=match,
            optimized_resume=resume,
            generated_cover_letter=cl,
        )
        assert pkg1.id == pkg2.id

    def test_skip_cache(self):
        job = make_mock_job()
        service = ApplicationPackageService()
        pkg1 = service.generate(job_posting=job, skip_cache=True)
        pkg2 = service.generate(job_posting=job, skip_cache=True)
        assert pkg1.id != pkg2.id

    def test_invalidate_cache(self):
        job = make_mock_job()
        profile = make_mock_profile()
        service = ApplicationPackageService()
        pkg1 = service.generate(
            job_posting=job,
            profile_intelligence=profile,
        )
        service.invalidate_cache(
            profile_hash="prof123",
            job_hash=PackageGenerator.compute_job_hash(job),
        )
        pkg2 = service.generate(
            job_posting=job,
            profile_intelligence=profile,
        )
        assert pkg1.id != pkg2.id

    def test_clear_cache(self):
        job = make_mock_job()
        service = ApplicationPackageService()
        service.generate(job_posting=job)
        service.clear_cache()
        pkg2 = service.generate(job_posting=job)
        assert pkg2 is not None

    def test_minimal_input(self):
        service = ApplicationPackageService()
        pkg = service.generate(job_posting=make_mock_job())
        assert pkg.completeness_score == 15
        assert pkg.status == PackageStatus.INCOMPLETE

    def test_no_input(self):
        service = ApplicationPackageService()
        pkg = service.generate()
        assert pkg.validation.has_job_posting is False
        assert pkg.status == PackageStatus.INCOMPLETE


# ===========================================================================
# Schema Tests
# ===========================================================================


class TestSchemas:
    def test_application_package_defaults(self):
        pkg = ApplicationPackage()
        assert pkg.id is not None
        assert pkg.created_at is not None
        assert pkg.version == "1.0.0"
        assert pkg.completeness_score == 0
        assert pkg.status == PackageStatus.INCOMPLETE
        assert pkg.warnings == []

    def test_package_validation_defaults(self):
        v = PackageValidation()
        assert v.all_inputs_present is False
        assert v.has_job_posting is False
        assert v.warnings == []

    def test_package_with_all_fields(self):
        job = make_mock_job()
        pkg = ApplicationPackage(
            job=job,
            completeness_score=100,
            status=PackageStatus.COMPLETE,
            warnings=["Test warning"],
        )
        assert pkg.job is job
        assert pkg.completeness_score == 100
        assert pkg.status == PackageStatus.COMPLETE
        assert "Test warning" in pkg.warnings


# ===========================================================================
# Package Status Enum Tests
# ===========================================================================


class TestPackageStatus:
    def test_status_values(self):
        assert PackageStatus.COMPLETE.value == "complete"
        assert PackageStatus.PARTIAL.value == "partial"
        assert PackageStatus.INCOMPLETE.value == "incomplete"
