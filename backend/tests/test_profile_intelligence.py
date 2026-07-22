from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.profile_intelligence.completeness import ProfileCompletenessScorer
from app.profile_intelligence.extractor import ProfileExtractor
from app.profile_intelligence.schemas import (
    Availability,
    CareerLevel,
    UserIntelligenceProfile,
)
from app.profile_intelligence.summarizer import ProfileSummarizer
from app.profile_intelligence.validator import ProfileValidator


class TestProfileExtractor:
    def make_skill(self, name="Python", proficiency="expert", years=5.0, category="Language"):
        s = MagicMock()
        s.name = name
        s.proficiency = proficiency
        s.years_experience = years
        s.category = category
        return s

    def make_exp(
        self, title="Engineer", company="Acme", start=None, end=None,
        currently=False, achievements=None, industry="Tech",
    ):
        e = MagicMock()
        e.title = title
        e.company = company
        e.start_date = start or datetime(2020, 1, 1, tzinfo=timezone.utc)
        e.end_date = end or datetime(2023, 1, 1, tzinfo=timezone.utc)
        e.currently_working = currently
        e.achievements = achievements or []
        e.responsibilities = []
        e.industry = industry
        e.description = ""
        return e

    def make_edu(self, degree="B.Sc.", field="Computer Science", institution="MIT"):
        e = MagicMock()
        e.degree = degree
        e.field_of_study = field
        e.institution = institution
        e.start_date = datetime(2016, 1, 1, tzinfo=timezone.utc)
        e.end_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        return e

    def make_cert(self, name="AWS Solutions Architect", issuer="Amazon"):
        c = MagicMock()
        c.name = name
        c.issuer = issuer
        return c

    def test_extract_primary_skills_empty(self):
        extractor = ProfileExtractor()
        primary, secondary = extractor.extract_primary_skills([], [], [])
        assert primary == []
        assert secondary == []

    def test_extract_primary_skills_orders_by_priority(self):
        extractor = ProfileExtractor()
        skills = ["Python", "SQL", "React", "AWS", "Docker", "Kubernetes", "Git", "Linux"]
        profs = ["expert", "advanced", "intermediate", "intermediate", "intermediate", None, None, None]
        years = [8.0, 5.0, 3.0, 2.0, 2.0, 1.0, 5.0, 3.0]
        primary, secondary = extractor.extract_primary_skills(skills, profs, years)
        assert len(primary) <= 5
        assert "Python" in primary
        assert "SQL" in primary or "React" in primary

    def test_extract_primary_skills_deduplicates(self):
        extractor = ProfileExtractor()
        skills = ["Python", "python", "PYTHON", "React", "react"]
        primary, secondary = extractor.extract_primary_skills(skills, [None] * 5, [1.0] * 5)
        all_skills = set(s.lower() for s in primary + secondary)
        assert len(all_skills) == 2

    def test_classify_technical_stack(self):
        extractor = ProfileExtractor()
        skills = ["Python", "React", "PostgreSQL", "AWS", "Docker", "Git", "Jira", "Figma"]
        stack = extractor.classify_technical_stack(skills)
        assert "Python" in stack.programming_languages
        assert "React" in stack.frameworks
        assert "PostgreSQL" in stack.databases
        assert "AWS" in stack.cloud_platforms
        assert "Git" in stack.tools

    def test_infer_career_level_by_years(self):
        extractor = ProfileExtractor()
        assert extractor.infer_career_level("Engineer", 0.5) == CareerLevel.ENTRY
        assert extractor.infer_career_level("Engineer", 2.0) == CareerLevel.JUNIOR
        assert extractor.infer_career_level("Engineer", 4.0) == CareerLevel.MID
        assert extractor.infer_career_level("Engineer", 7.0) == CareerLevel.SENIOR
        assert extractor.infer_career_level("Engineer", 12.0) == CareerLevel.LEAD
        assert extractor.infer_career_level("Engineer", 16.0) == CareerLevel.EXECUTIVE

    def test_infer_career_level_by_role(self):
        extractor = ProfileExtractor()
        assert extractor.infer_career_level("Junior Developer", None) == CareerLevel.JUNIOR
        assert extractor.infer_career_level("Senior Developer", None) == CareerLevel.SENIOR
        assert extractor.infer_career_level("Lead Developer", None) == CareerLevel.LEAD
        assert extractor.infer_career_level("CTO", None) == CareerLevel.EXECUTIVE
        assert extractor.infer_career_level("Intern", None) == CareerLevel.ENTRY

    def test_infer_availability(self):
        extractor = ProfileExtractor()
        assert extractor.infer_availability("immediate") == Availability.IMMEDIATE
        assert extractor.infer_availability("15 days") == Availability.TWO_WEEKS
        assert extractor.infer_availability("1 month") == Availability.ONE_MONTH
        assert extractor.infer_availability("90 days") == Availability.THREE_MONTHS
        assert extractor.infer_availability(None) == Availability.UNKNOWN
        assert extractor.infer_availability("") == Availability.UNKNOWN

    def test_extract_industries_dedup(self):
        extractor = ProfileExtractor()
        e1 = self.make_exp(industry="Technology")
        e2 = self.make_exp(title="Manager", company="Beta", industry="Technology")
        e3 = self.make_exp(title="Consultant", company="Gamma", industry="Finance")
        result = extractor.extract_industries([e1, e2, e3])
        assert result == ["Technology", "Finance"]

    def test_extract_projects(self):
        extractor = ProfileExtractor()
        p1 = MagicMock()
        p1.name = "Project Alpha"
        p2 = MagicMock()
        p2.name = "Project Beta"
        result = extractor.extract_projects([p1, p2])
        assert result == ["Project Alpha", "Project Beta"]

    def test_extract_certifications_with_issuer(self):
        extractor = ProfileExtractor()
        certs = [self.make_cert("AWS SA", "Amazon"), self.make_cert("PMP", "PMI")]
        result = extractor.extract_certifications(certs)
        assert "AWS SA (Amazon)" in result
        assert "PMP (PMI)" in result

    def test_extract_education_summary_highest_degree(self):
        extractor = ProfileExtractor()
        edu_list = [
            self.make_edu("B.Sc.", "CS", "MIT"),
            self.make_edu("M.Sc.", "AI", "Stanford"),
        ]
        result = extractor.extract_education_summary(edu_list)
        assert result is not None
        assert "M.Sc." in result
        assert "AI" in result
        assert "Stanford" in result

    def test_extract_education_summary_empty(self):
        extractor = ProfileExtractor()
        assert extractor.extract_education_summary([]) is None

    def test_extract_education_summary_single(self):
        extractor = ProfileExtractor()
        edu = [self.make_edu("B.E.", "Computer Science", "IIT")]
        result = extractor.extract_education_summary(edu)
        assert result is not None
        assert "B.E." in result

    def test_extract_languages_dedups(self):
        extractor = ProfileExtractor()
        l1 = MagicMock()
        l1.language = "English"
        l1.proficiency = "Native"
        l2 = MagicMock()
        l2.language = "English"
        l2.proficiency = "C2"
        result = extractor.extract_languages([l1, l2])
        assert len(result) == 1
        assert result[0].language == "English"

    def test_extract_skill_names(self):
        extractor = ProfileExtractor()
        skills = [self.make_skill("Python"), self.make_skill("Java")]
        result = extractor.extract_skill_names(skills)
        assert result == ["Python", "Java"]

    def test_extract_years_from_profile(self):
        extractor = ProfileExtractor()
        profile = MagicMock()
        profile.total_years_experience = 8.0
        result = extractor.extract_years_of_experience(profile, [])
        assert result == 8.0

    def test_extract_years_from_experiences(self):
        extractor = ProfileExtractor()
        e1 = self.make_exp(
            start=datetime(2017, 1, 1, tzinfo=timezone.utc),
            end=datetime(2022, 1, 1, tzinfo=timezone.utc),
        )
        profile = MagicMock()
        profile.total_years_experience = None
        result = extractor.extract_years_of_experience(profile, [e1])
        assert result is not None
        assert result >= 4.9
        assert result <= 5.1

    def test_extract_salary_expectation(self):
        extractor = ProfileExtractor()
        profile = MagicMock()
        profile.expected_salary = 100000.0
        prefs = MagicMock()
        prefs.minimum_salary = None
        result = extractor.extract_salary_expectation(profile, prefs)
        assert result is not None
        assert "100,000" in result

    def test_extract_salary_expectation_from_prefs(self):
        extractor = ProfileExtractor()
        prefs = MagicMock()
        prefs.minimum_salary = 120000.0
        prefs.preferred_currency = "USD"
        result = extractor.extract_salary_expectation(None, prefs)
        assert result is not None
        assert "120,000" in result

    def test_extract_employment_preference(self):
        extractor = ProfileExtractor()
        prefs = MagicMock()
        prefs.employment_types = ["full_time", "contract"]
        result = extractor.extract_employment_preference(prefs)
        assert result is not None
        assert "Full Time" in result

    def test_extract_preferred_locations(self):
        extractor = ProfileExtractor()
        prefs = MagicMock()
        prefs.preferred_locations = ["San Francisco, CA", "Remote"]
        result = extractor.extract_preferred_locations(prefs)
        assert result == ["San Francisco, CA", "Remote"]

    def test_extract_remote_preference_true(self):
        extractor = ProfileExtractor()
        prefs = MagicMock()
        prefs.work_modes = ["remote", "hybrid"]
        assert extractor.extract_remote_preference(prefs) is True

    def test_extract_remote_preference_false(self):
        extractor = ProfileExtractor()
        prefs = MagicMock()
        prefs.work_modes = ["on_site"]
        assert extractor.extract_remote_preference(prefs) is False

    def test_extract_strengths_from_achievements(self):
        extractor = ProfileExtractor()
        e1 = self.make_exp(achievements=["Led team to 30% revenue growth", "Built CI/CD pipeline"])
        e2 = self.make_exp(title="Manager", achievements=["Managed 10 engineers"])
        result = extractor.extract_strengths([], [e1, e2])
        assert len(result) >= 3
        assert "Led team to 30% revenue growth" in result

    def test_extract_strengths_from_expert_skills(self):
        extractor = ProfileExtractor()
        s1 = self.make_skill("Python", proficiency="expert")
        s2 = self.make_skill("Docker", proficiency="advanced")
        s3 = self.make_skill("Git", proficiency="beginner")
        result = extractor.extract_strengths([s1, s2, s3], [])
        assert any("Expert in Python" in s for s in result)
        assert any("Expert in Docker" in s for s in result)

    def test_extract_career_goals_desired_role(self):
        extractor = ProfileExtractor()
        profile = MagicMock()
        profile.desired_role = "Senior Engineer"
        profile.professional_summary = None
        result = extractor.extract_career_goals(profile)
        assert "Seeking" in result
        assert "Senior Engineer" in result

    def test_extract_career_goals_none(self):
        extractor = ProfileExtractor()
        assert extractor.extract_career_goals(None) is None

    def test_normalize_skill_synonym(self):
        extractor = ProfileExtractor()
        assert extractor._normalize_skill("reactjs") == "react"
        assert extractor._normalize_skill("golang") == "go"
        assert extractor._normalize_skill("UnknownSkill") == "UnknownSkill"

    def test_deduplicate_skills(self):
        extractor = ProfileExtractor()
        result = extractor._deduplicate_skills(["Python", "python", "Python", "Java"])
        assert result == ["Python", "Java"]


class TestProfileCompletenessScorer:
    def make_profile(self, **kwargs):
        p = MagicMock()
        for k, v in kwargs.items():
            setattr(p, k, v)
        return p

    def test_compute_empty(self):
        scorer = ProfileCompletenessScorer()
        result = scorer.compute({"profile": None, "skills": [], "education": [], "experience": []})
        assert result.overall_score == 0
        assert "skills" in result.missing_items

    def test_compute_full_profile(self):
        scorer = ProfileCompletenessScorer()
        profile = self.make_profile(
            headline="Senior Engineer",
            professional_summary="Summary",
            current_role="Engineer",
            total_years_experience=5.0,
            desired_role="Senior",
            employment_status="employed",
            notice_period="30 days",
            portfolio_url="https://example.com",
            linkedin_url="https://linkedin.com/in/user",
            github_url="https://github.com/user",
        )
        skill = MagicMock()
        skill.name = "Python"
        skill.proficiency = "expert"
        skill.category = "Language"
        skill.years_experience = 5.0
        edu = MagicMock()
        edu.degree = "B.Sc."
        edu.field_of_study = "CS"
        edu.institution = "MIT"
        exp = MagicMock()
        exp.title = "Engineer"
        exp.company = "Acme"
        exp.responsibilities = ["Coding"]
        exp.achievements = ["Shipped product"]
        lang = MagicMock()
        lang.language = "English"
        lang.proficiency = "Native"
        cert = MagicMock()
        cert.name = "AWS"
        cert.issuer = "Amazon"
        cert.credential_url = "https://aws.com/cert"
        prefs = MagicMock()
        prefs.preferred_titles = ["Engineer"]
        prefs.preferred_locations = ["Remote"]
        prefs.employment_types = ["full_time"]
        prefs.work_modes = ["remote"]
        prefs.minimum_salary = 100000.0

        skill2 = MagicMock()
        skill2.name = "Docker"
        skill2.proficiency = "intermediate"
        skill2.category = "Tools"

        raw = {
            "profile": profile,
            "skills": [skill, skill2],
            "education": [edu],
            "experience": [exp],
            "projects": [],
            "certifications": [cert],
            "languages": [lang],
            "social_links": [],
            "preferences": prefs,
        }
        result = scorer.compute(raw)
        assert result.overall_score >= 60
        assert "skills" not in result.missing_items

    def test_missing_items(self):
        scorer = ProfileCompletenessScorer()
        profile = self.make_profile()
        raw = {
            "profile": profile, "skills": [], "education": [],
            "experience": [], "projects": [], "certifications": [],
            "languages": [], "social_links": [], "preferences": None,
        }
        result = scorer.compute(raw)
        assert len(result.missing_items) > 0


class TestProfileValidator:
    def make_skill(self, name="Python"):
        s = MagicMock()
        s.name = name
        return s

    def make_exp(self, title="Engineer", company="Acme", start=None, end=None, currently=False):
        e = MagicMock()
        e.title = title
        e.company = company
        e.start_date = start
        e.end_date = end
        e.currently_working = currently
        return e

    def test_validate_empty(self):
        validator = ProfileValidator()
        result = validator.validate({})
        assert any("No career profile" in w for w in result.warnings)

    def test_validate_missing_skills(self):
        validator = ProfileValidator()
        profile = MagicMock()
        profile.headline = "Engineer"
        profile.professional_summary = "Summary"
        result = validator.validate({"profile": profile, "skills": []})
        assert any("No skills" in i.message for i in result.issues)

    def test_validate_duplicate_skills(self):
        validator = ProfileValidator()
        profile = MagicMock()
        profile.headline = "Engineer"
        s1 = self.make_skill("Python")
        s2 = self.make_skill("Python")
        result = validator.validate({"profile": profile, "skills": [s1, s2]})
        assert any("Duplicate" in i.message for i in result.issues)

    def test_validate_incomplete_work_history(self):
        validator = ProfileValidator()
        profile = MagicMock()
        profile.headline = "Engineer"
        exp = self.make_exp(start=None, end=None, currently=False)
        result = validator.validate({"profile": profile, "experience": [exp], "skills": [self.make_skill()]})
        assert any("Missing start date" in i.message for i in result.issues)
        assert any("Missing end date" in i.message for i in result.issues)

    def test_validate_future_end_date(self):
        validator = ProfileValidator()
        profile = MagicMock()
        profile.headline = "Engineer"
        future = datetime(2030, 1, 1, tzinfo=timezone.utc)
        exp = self.make_exp(start=datetime(2020, 1, 1, tzinfo=timezone.utc), end=future, currently=False)
        result = validator.validate({"profile": profile, "experience": [exp], "skills": [self.make_skill()]})
        assert any("future" in i.message.lower() for i in result.issues)

    def test_validate_missing_resume(self):
        validator = ProfileValidator()
        profile = MagicMock()
        profile.headline = "Engineer"
        result = validator.validate({"profile": profile, "skills": [self.make_skill()], "has_resume": False})
        assert any("No resume" in w for w in result.warnings)

    def test_validate_no_missing_resume_warning(self):
        validator = ProfileValidator()
        profile = MagicMock()
        profile.headline = "Engineer"
        result = validator.validate({"profile": profile, "skills": [self.make_skill()], "has_resume": True})
        assert not any("No resume" in w for w in result.warnings)

    def test_validate_conflicting_employment(self):
        validator = ProfileValidator()
        profile = MagicMock()
        profile.headline = "Engineer"
        profile.employment_status = "unemployed"
        profile.current_role = "Senior Engineer"
        profile.professional_summary = ""
        result = validator.validate({"profile": profile, "skills": [self.make_skill()], "has_resume": True})
        assert any("unemployed" in w.lower() and "current role" in w.lower() for w in result.warnings)


class TestProfileSummarizer:
    def make_profile(self, **kwargs):
        return UserIntelligenceProfile(
            user_id=uuid.uuid4(),
            **kwargs,
        )

    def test_generate_personal_summary_with_role_and_years(self):
        summarizer = ProfileSummarizer()
        profile = self.make_profile(
            current_role="Software Engineer",
            years_of_experience=5.0,
            career_level=CareerLevel.MID,
            primary_skills=["Python", "SQL", "React"],
            industries=["Technology", "Finance"],
            preferred_locations=["San Francisco, CA"],
        )
        summary = summarizer.generate_personal_summary(profile)
        assert summary is not None
        assert "Software Engineer" in summary
        assert "5" in summary
        assert "Python" in summary
        assert "Technology" in summary

    def test_generate_personal_summary_minimal(self):
        summarizer = ProfileSummarizer()
        profile = self.make_profile(
            current_role="Developer",
            years_of_experience=None,
            career_level=CareerLevel.UNKNOWN,
        )
        summary = summarizer.generate_personal_summary(profile)
        assert summary is not None
        assert "Developer" in summary

    def test_generate_personal_summary_empty(self):
        summarizer = ProfileSummarizer()
        profile = self.make_profile()
        summary = summarizer.generate_personal_summary(profile)
        assert summary is None


class TestProfileIntelligenceService:
    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_session):
        from app.profile_intelligence.service import ProfileIntelligenceService

        return ProfileIntelligenceService(
            session=mock_session,
            cache_ttl_seconds=60,
        )

    def test_get_cached_none(self, service):
        assert service._get_cached("nonexistent") is None

    def test_cache_set_and_get(self, service):
        profile = UserIntelligenceProfile(user_id=uuid.uuid4())
        service._set_cache("test_key", profile)
        cached = service._get_cached("test_key")
        assert cached is not None
        assert cached.user_id == profile.user_id

    def test_cache_ttl_expiry(self, service):
        service._cache_ttl = 0
        profile = UserIntelligenceProfile(user_id=uuid.uuid4())
        service._set_cache("test_key", profile)
        cached = service._get_cached("test_key")
        assert cached is None

    def test_invalidate_cache(self, service):
        profile = UserIntelligenceProfile(user_id=uuid.uuid4())
        uid = str(profile.user_id)
        service._set_cache(uid, profile)
        service.invalidate_cache(profile.user_id)
        assert service._get_cached(uid) is None

    def test_clear_cache(self, service):
        profile = UserIntelligenceProfile(user_id=uuid.uuid4())
        service._set_cache("a", profile)
        service._set_cache("b", profile)
        service.clear_cache()
        assert service._get_cached("a") is None
        assert service._get_cached("b") is None

    @patch("app.profile_intelligence.service.CareerProfileRepository")
    @patch("app.profile_intelligence.service.ResumeVersionRepository")
    async def test_get_profile_intelligence(self, mock_resume_repo, mock_profile_repo, service):
        user_id = uuid.uuid4()
        profile = MagicMock()
        profile.headline = "Senior Engineer"
        profile.professional_summary = "Summary"
        profile.current_role = "Engineer"
        profile.total_years_experience = 5.0
        profile.desired_role = "Senior"
        profile.employment_status = "employed"
        profile.notice_period = "30 days"
        profile.portfolio_url = None
        profile.linkedin_url = None
        profile.github_url = None
        profile.website_url = None
        profile.expected_salary = 100000.0
        profile.willing_to_relocate = None
        profile.experience = []
        profile.education = []
        profile.projects = []
        profile.skills = []
        profile.certifications = []
        profile.languages = []
        profile.social_links = []
        profile.preferences = None

        service._profile_repo.get_by_user = AsyncMock(return_value=profile)
        service._resume_repo.list_by_user = AsyncMock(return_value=[])

        result = await service.get_profile_intelligence(user_id)
        assert result.user_id == user_id
        assert result.current_role == "Engineer"
        assert result.years_of_experience == 5.0
        assert result.career_level == CareerLevel.MID
        assert result.completeness.overall_score >= 0

    @patch("app.profile_intelligence.service.CareerProfileRepository")
    @patch("app.profile_intelligence.service.ResumeVersionRepository")
    async def test_get_profile_intelligence_caching(self, mock_resume_repo, mock_profile_repo, service):
        user_id = uuid.uuid4()
        profile = MagicMock()
        profile.headline = None
        profile.professional_summary = None
        profile.current_role = None
        profile.total_years_experience = None
        profile.desired_role = None
        profile.employment_status = None
        profile.notice_period = None
        profile.portfolio_url = None
        profile.linkedin_url = None
        profile.github_url = None
        profile.website_url = None
        profile.expected_salary = None
        profile.willing_to_relocate = None
        profile.experience = []
        profile.education = []
        profile.projects = []
        profile.skills = []
        profile.certifications = []
        profile.languages = []
        profile.social_links = []
        profile.preferences = None

        service._profile_repo.get_by_user = AsyncMock(return_value=profile)
        service._resume_repo.list_by_user = AsyncMock(return_value=[])

        result1 = await service.get_profile_intelligence(user_id)
        result2 = await service.get_profile_intelligence(user_id)
        assert result1.profile_hash == result2.profile_hash

    @patch("app.profile_intelligence.service.CareerProfileRepository")
    @patch("app.profile_intelligence.service.ResumeVersionRepository")
    async def test_get_profile_intelligence_skip_cache(self, mock_resume_repo, mock_profile_repo, service):
        user_id = uuid.uuid4()
        profile = MagicMock()
        profile.headline = None
        profile.professional_summary = None
        profile.current_role = None
        profile.total_years_experience = None
        profile.desired_role = None
        profile.employment_status = None
        profile.notice_period = None
        profile.portfolio_url = None
        profile.linkedin_url = None
        profile.github_url = None
        profile.website_url = None
        profile.expected_salary = None
        profile.willing_to_relocate = None
        profile.experience = []
        profile.education = []
        profile.projects = []
        profile.skills = []
        profile.certifications = []
        profile.languages = []
        profile.social_links = []
        profile.preferences = None

        service._profile_repo.get_by_user = AsyncMock(return_value=profile)
        service._resume_repo.list_by_user = AsyncMock(return_value=[])

        result = await service.get_profile_intelligence(user_id, skip_cache=True)
        assert result.user_id == user_id

    def test_compute_hash_deterministic(self, service):
        profile = UserIntelligenceProfile(user_id=uuid.uuid4())
        h1 = service._compute_hash(profile)
        h2 = service._compute_hash(profile)
        assert h1 == h2

    def test_compute_hash_different_profiles(self, service):
        p1 = UserIntelligenceProfile(user_id=uuid.uuid4(), current_role="A")
        p2 = UserIntelligenceProfile(user_id=uuid.uuid4(), current_role="B")
        assert service._compute_hash(p1) != service._compute_hash(p2)
