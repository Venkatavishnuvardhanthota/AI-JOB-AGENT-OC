import uuid
from datetime import date

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.profile import router as profile_router
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import create_access_token, get_password_hash
from app.schemas.achievement import AchievementCreate, AchievementUpdate
from app.schemas.career_profile import CareerProfileUpdate, SalaryPreference
from app.schemas.certification import CertificationCreate
from app.schemas.education import EducationCreate, EducationUpdate
from app.schemas.experience import ExperienceCreate
from app.schemas.project import ProjectCreate
from app.schemas.social_link import SocialLinkCreate, SocialLinkResponse
from app.services.profile import CareerProfileService
from database.models.achievement import Achievement
from database.models.career_profile import CareerProfile
from database.models.education import Education
from database.models.experience import Experience
from database.models.language import Language
from database.models.project import Project
from database.models.skill import Skill
from database.models.social_link import SocialLink
from database.models.user import User
from database.repositories import (
    AchievementRepository,
    CareerProfileRepository,
    CertificationRepository,
    EducationRepository,
    ExperienceRepository,
    LanguageRepository,
    ProjectRepository,
    SkillRepository,
    SocialLinkRepository,
    UserRepository,
)

# ── Helpers ──


async def _create_user(session: AsyncSession, email: str = "profile@test.com") -> User:
    repo = UserRepository(session)
    user = User(
        email=email,
        password_hash=get_password_hash("TestPass123!"),
        first_name="Test",
        last_name="User",
    )
    return await repo.create(user)


async def _create_profile(session: AsyncSession, user_id: uuid.UUID) -> CareerProfile:
    repo = CareerProfileRepository(session)
    profile = CareerProfile(user_id=user_id)
    return await repo.create(profile)


async def _create_full_profile(session: AsyncSession, user_id: uuid.UUID) -> CareerProfile:
    profile = await _create_profile(session, user_id)
    edu_repo = EducationRepository(session)
    edu = Education(profile_id=profile.id, institution="MIT", degree="BS", field_of_study="CS")
    await edu_repo.create(edu)
    exp_repo = ExperienceRepository(session)
    exp = Experience(profile_id=profile.id, company="Google", title="Engineer")
    await exp_repo.create(exp)
    skill_repo = SkillRepository(session)
    skill = Skill(profile_id=profile.id, name="Python")
    await skill_repo.create(skill)
    proj_repo = ProjectRepository(session)
    proj = Project(profile_id=profile.id, name="My Project")
    await proj_repo.create(proj)
    return profile


# ── Model Tests ──


class TestCareerProfileModel:
    async def test_create_with_new_fields(self, session):
        user = await _create_user(session)
        profile = CareerProfile(
            user_id=user.id,
            headline="Senior Developer",
            total_years_experience=8.5,
            current_role="Senior Engineer",
            desired_role="Lead Developer",
            employment_status="employed",
            current_salary=120000.00,
            expected_salary=150000.00,
            salary_preference="paid_only",
            willing_to_relocate=True,
            visa_sponsorship_requirement=False,
            notice_period="2 weeks",
        )
        session.add(profile)
        await session.flush()
        assert profile.headline == "Senior Developer"
        assert profile.current_role == "Senior Engineer"
        assert profile.salary_preference == "paid_only"

    async def test_default_profile_completeness(self, session):
        user = await _create_user(session)
        profile = CareerProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
        assert profile.profile_completeness == 0


class TestAchievementModel:
    async def test_create_achievement(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        achievement = Achievement(
            profile_id=profile.id,
            title="Hackathon Winner",
            organization="TechConf",
            achievement_type="Hackathon Winner",
            date=date(2026, 3, 1),
            description="Won first place",
            url="https://example.com/hackathon",
        )
        session.add(achievement)
        await session.flush()
        assert achievement.id is not None
        assert achievement.title == "Hackathon Winner"

    async def test_cascade_delete(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        achievement = Achievement(profile_id=profile.id, title="Award")
        session.add(achievement)
        await session.flush()
        achievement_id = achievement.id
        await session.delete(profile)
        await session.flush()
        deleted = await session.get(Achievement, achievement_id)
        assert deleted is None


class TestSocialLinkModel:
    async def test_create_social_link(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        link = SocialLink(profile_id=profile.id, platform="github", url="https://github.com/test")
        session.add(link)
        await session.flush()
        assert link.id is not None
        assert link.platform == "github"

    async def test_cascade_delete(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        link = SocialLink(profile_id=profile.id, platform="linkedin", url="https://linkedin.com/in/test")
        session.add(link)
        await session.flush()
        link_id = link.id
        await session.delete(profile)
        await session.flush()
        deleted = await session.get(SocialLink, link_id)
        assert deleted is None

    async def test_unique_platform_per_profile(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        repo = SocialLinkRepository(session)
        link = SocialLink(profile_id=profile.id, platform="github", url="https://github.com/a")
        await repo.create(link)
        duplicate = SocialLink(profile_id=profile.id, platform="github", url="https://github.com/b")
        with pytest.raises(Exception):
            await repo.create(duplicate)


class TestLanguageModel:
    async def test_unique_language_per_profile(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        repo = LanguageRepository(session)
        lang = Language(profile_id=profile.id, language="English")
        await repo.create(lang)
        duplicate = Language(profile_id=profile.id, language="English")
        with pytest.raises(Exception):
            await repo.create(duplicate)


class TestEducationNewFields:
    async def test_location_and_cgpa(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        edu = Education(
            profile_id=profile.id,
            institution="MIT",
            degree="BS",
            location="Cambridge, MA",
            cgpa="3.8",
            currently_studying=True,
        )
        session.add(edu)
        await session.flush()
        assert edu.location == "Cambridge, MA"
        assert edu.cgpa == "3.8"
        assert edu.currently_studying is True
        assert not hasattr(edu, "description")


class TestExperienceNewFields:
    async def test_new_list_fields(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        exp = Experience(
            profile_id=profile.id,
            company="Google",
            title="Engineer",
            responsibilities=["Team lead", "Code reviews"],
            achievements=["Shipped product"],
            technologies_used=["Python", "React"],
        )
        session.add(exp)
        await session.flush()
        assert exp.responsibilities == ["Team lead", "Code reviews"]
        assert exp.achievements == ["Shipped product"]
        assert exp.technologies_used == ["Python", "React"]


class TestSkillNewFields:
    async def test_skill_level_and_order(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        skill = Skill(profile_id=profile.id, name="Python", skill_level="advanced", display_order=1)
        session.add(skill)
        await session.flush()
        assert skill.skill_level == "advanced"
        assert skill.display_order == 1


class TestProjectNewFields:
    async def test_dates_and_live_url(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        proj = Project(
            profile_id=profile.id,
            name="Portfolio",
            live_url="https://example.com",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 1),
        )
        session.add(proj)
        await session.flush()
        assert proj.live_url == "https://example.com"
        assert proj.start_date == date(2024, 1, 1)
        assert proj.end_date == date(2024, 6, 1)


# ── Repository Tests ──


class TestAchievementRepository:
    async def test_list_by_profile(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        repo = AchievementRepository(session)
        await repo.create(Achievement(profile_id=profile.id, title="Award A", display_order=2))
        await repo.create(Achievement(profile_id=profile.id, title="Award B", display_order=1))
        items = await repo.list_by_profile(profile.id)
        assert len(items) == 2
        assert items[0].title == "Award B"

    async def test_exists_by_title_case_insensitive(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        repo = AchievementRepository(session)
        await repo.create(Achievement(profile_id=profile.id, title="Hackathon Winner"))
        assert await repo.exists_by_title(profile.id, "hackathon winner") is True
        assert await repo.exists_by_title(profile.id, "Patent") is False


class TestSocialLinkRepository:
    async def test_list_by_profile(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        repo = SocialLinkRepository(session)
        link1 = SocialLink(profile_id=profile.id, platform="github", url="https://github.com/a", display_order=2)
        link2 = SocialLink(profile_id=profile.id, platform="linkedin", url="https://linkedin.com/in/a", display_order=1)
        await repo.create(link1)
        await repo.create(link2)
        links = await repo.list_by_profile(profile.id)
        assert len(links) == 2
        assert links[0].platform == "linkedin"
        assert links[1].platform == "github"

    async def test_exists_by_platform(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        repo = SocialLinkRepository(session)
        link = SocialLink(profile_id=profile.id, platform="github", url="https://github.com/a")
        await repo.create(link)
        assert await repo.exists_by_platform(profile.id, "github") is True
        assert await repo.exists_by_platform(profile.id, "twitter") is False


# ── Schema Validation Tests ──


class TestSocialLinkValidation:
    def test_valid_url(self):
        link = SocialLinkCreate(platform="GitHub", url="https://github.com/test")
        assert link.url == "https://github.com/test"
        assert link.platform == "github"

    def test_invalid_url(self):
        with pytest.raises(PydanticValidationError, match="URL must start with"):
            SocialLinkCreate(platform="github", url="ftp://invalid.com")

    def test_invalid_url_no_scheme(self):
        with pytest.raises(PydanticValidationError, match="URL must start with"):
            SocialLinkCreate(platform="github", url="github.com/test")

    def test_invalid_platform(self):
        with pytest.raises(PydanticValidationError, match="Platform must be one of"):
            SocialLinkCreate(platform="twitter", url="https://twitter.com/test")


class TestCareerProfileUpdateValidation:
    def test_valid_urls(self):
        data = CareerProfileUpdate(linkedin_url="https://linkedin.com/in/test")
        assert data.linkedin_url == "https://linkedin.com/in/test"

    def test_invalid_urls(self):
        with pytest.raises(PydanticValidationError, match="URL must start with"):
            CareerProfileUpdate(portfolio_url="not-a-url")

    def test_total_years_experience_range(self):
        with pytest.raises(PydanticValidationError):
            CareerProfileUpdate(total_years_experience=-1)

    def test_salary_preference_valid(self):
        data = CareerProfileUpdate(salary_preference=SalaryPreference.PAID_PREFERRED)
        assert data.salary_preference == "paid_preferred"

    def test_salary_preference_invalid(self):
        with pytest.raises(PydanticValidationError):
            CareerProfileUpdate(salary_preference="unpaid")


class TestEducationValidation:
    def test_end_date_before_start_date_raises(self):
        with pytest.raises(PydanticValidationError, match="End date must be on or after the start date"):
            EducationCreate(
                institution="MIT",
                degree="BS",
                start_date=date(2024, 6, 1),
                end_date=date(2024, 1, 1),
            )

    def test_valid_dates(self):
        edu = EducationCreate(
            institution="MIT",
            degree="BS",
            location="Cambridge, MA",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 1),
        )
        assert edu.location == "Cambridge, MA"

    def test_remove_description_field(self):
        edu = EducationCreate(institution="MIT", degree="BS")
        assert not hasattr(edu, "description")

    def test_update_end_date_before_start_date_raises(self):
        with pytest.raises(PydanticValidationError):
            EducationUpdate(institution="MIT", start_date=date(2024, 6, 1), end_date=date(2024, 1, 1))


class TestExperienceValidation:
    def test_end_date_before_start_date_raises(self):
        with pytest.raises(PydanticValidationError, match="End date must be on or after the start date"):
            ExperienceCreate(
                company="Google",
                title="Engineer",
                start_date=date(2024, 6, 1),
                end_date=date(2024, 1, 1),
            )

    def test_current_job_rejects_end_date(self):
        with pytest.raises(PydanticValidationError, match="End date must be empty"):
            ExperienceCreate(
                company="Google",
                title="Engineer",
                currently_working=True,
                end_date=date(2024, 6, 1),
            )

    def test_current_job_allows_no_end_date(self):
        exp = ExperienceCreate(company="Google", title="Engineer", currently_working=True)
        assert exp.currently_working is True


class TestProjectValidation:
    def test_end_date_before_start_date_raises(self):
        with pytest.raises(PydanticValidationError):
            ProjectCreate(name="P", start_date=date(2024, 6, 1), end_date=date(2024, 1, 1))

    def test_invalid_url_raises(self):
        with pytest.raises(PydanticValidationError, match="URL must start with"):
            ProjectCreate(name="P", github_url="example.com/foo")

    def test_valid_urls(self):
        proj = ProjectCreate(name="P", github_url="https://github.com/a", live_url="https://example.com")
        assert proj.github_url == "https://github.com/a"


class TestCertificationValidation:
    def test_expiration_before_issue_raises(self):
        with pytest.raises(PydanticValidationError, match="Expiration date must be on or after the issue date"):
            CertificationCreate(
                name="AWS",
                issue_date=date(2024, 6, 1),
                expiration_date=date(2024, 1, 1),
            )

    def test_invalid_credential_url_raises(self):
        with pytest.raises(PydanticValidationError, match="URL must start with"):
            CertificationCreate(name="AWS", credential_url="not-a-url")

    def test_valid_fields(self):
        cert = CertificationCreate(
            name="AWS",
            issuer="Amazon",
            credential_id="AWS-123",
            issue_date=date(2024, 1, 1),
            expiration_date=date(2025, 1, 1),
            credential_url="https://credential.com/aws-123",
        )
        assert cert.credential_id == "AWS-123"


class TestAchievementValidation:
    def test_invalid_url_raises(self):
        with pytest.raises(PydanticValidationError, match="URL must start with"):
            AchievementCreate(title="Award", url="example.com/award")

    def test_valid_create(self):
        achievement = AchievementCreate(
            title="Hackathon Winner",
            organization="TechConf",
            achievement_type="Hackathon Winner",
            date=date(2026, 3, 1),
            url="https://example.com",
        )
        assert achievement.title == "Hackathon Winner"

    def test_invalid_update_url(self):
        with pytest.raises(PydanticValidationError):
            AchievementUpdate(title="Award", url="ftp://bad")


# ── Service Tests ──


class TestCareerProfileService:
    async def test_get_or_create_profile(self, db_session):
        service = CareerProfileService(db_session)
        user = await _create_user(db_session)
        profile = await service.get_profile(user.id)
        assert profile is not None
        assert profile.user_id == user.id

    async def test_get_existing_profile(self, db_session):
        user = await _create_user(db_session)
        profile = await _create_profile(db_session, user.id)
        service = CareerProfileService(db_session)
        result = await service.get_profile(user.id)
        assert result.id == profile.id

    async def test_update_profile_fields(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        data = {
            "headline": "Senior Developer",
            "professional_summary": "Experienced developer",
            "total_years_experience": 10,
            "current_role": "Senior Engineer",
            "desired_role": "Lead",
            "employment_status": "employed",
            "current_salary": 100000,
            "expected_salary": 130000,
            "salary_preference": "paid_only",
            "willing_to_relocate": True,
            "visa_sponsorship_requirement": False,
            "notice_period": "1 month",
            "portfolio_url": "https://portfolio.com",
            "linkedin_url": "https://linkedin.com/in/test",
            "github_url": "https://github.com/test",
            "website_url": "https://example.com",
        }
        profile = await service.update_profile(user.id, data)
        assert profile.headline == "Senior Developer"
        assert profile.salary_preference == "paid_only"
        assert profile.total_years_experience == 10
        assert profile.willing_to_relocate is True

    async def test_partial_update(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        profile = await service.get_profile(user.id)
        assert profile.headline is None
        updated = await service.update_profile(user.id, {"headline": "Dev"})
        assert updated.headline == "Dev"
        assert updated.professional_summary is None

    async def test_update_profile_invalid_salary_preference(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        with pytest.raises(ValidationError, match="Invalid salary preference"):
            await service.update_profile(user.id, {"salary_preference": "unsure"})

    async def test_update_profile_paid_only_requires_minimum_salary(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        with pytest.raises(ValidationError, match="Minimum salary is required"):
            await service.update_profile(user.id, {"salary_preference": "paid_only"})

    async def test_update_profile_paid_only_with_salary_ok(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        profile = await service.update_profile(
            user.id, {"salary_preference": "paid_only", "expected_salary": 120000}
        )
        assert profile.salary_preference == "paid_only"
        assert profile.expected_salary == 120000

    # ── Education ──

    async def test_add_education(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        edu = await service.add_education(
            user.id,
            {"institution": "MIT", "degree": "BS", "field_of_study": "CS", "location": "Cambridge, MA"},
        )
        assert edu.id is not None
        assert edu.institution == "MIT"
        assert edu.location == "Cambridge, MA"
        assert edu.currently_studying is False

    async def test_add_education_with_currently_studying(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS", "currently_studying": True})
        assert edu.currently_studying is True

    async def test_add_education_end_before_start_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        with pytest.raises(ValidationError, match="End date must be on or after the start date"):
            await service.add_education(
                user.id,
                {
                    "institution": "MIT",
                    "degree": "BS",
                    "start_date": date(2024, 6, 1),
                    "end_date": date(2024, 1, 1),
                },
            )

    async def test_update_education_ownership(self, db_session):
        user = await _create_user(db_session)
        other_user = await _create_user(db_session, "other@test.com")
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        with pytest.raises(NotFoundError):
            await service.update_education(other_user.id, edu.id, {"institution": "Stanford"})

    async def test_delete_education_updates_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        completeness = await service.calculate_completeness(user.id)
        assert completeness["breakdown"]["education"] == 8
        await service.delete_education(user.id, edu.id)
        completeness = await service.calculate_completeness(user.id)
        assert completeness["breakdown"]["education"] == 0

    # ── Experience ──

    async def test_add_experience_with_new_fields(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        exp = await service.add_experience(
            user.id,
            {
                "company": "Google",
                "title": "Engineer",
                "responsibilities": ["Lead team"],
                "achievements": ["Shipped product"],
                "technologies_used": ["Python"],
            },
        )
        assert exp.responsibilities == ["Lead team"]
        assert exp.achievements == ["Shipped product"]
        assert exp.technologies_used == ["Python"]

    async def test_add_experience_current_job_rejects_end_date(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        with pytest.raises(ValidationError, match="End date must be empty"):
            await service.add_experience(
                user.id,
                {
                    "company": "Google",
                    "title": "Engineer",
                    "currently_working": True,
                    "end_date": date(2024, 6, 1),
                },
            )

    async def test_update_experience_ownership(self, db_session):
        user = await _create_user(db_session)
        other = await _create_user(db_session, "other2@test.com")
        service = CareerProfileService(db_session)
        exp = await service.add_experience(user.id, {"company": "G", "title": "E"})
        with pytest.raises(NotFoundError):
            await service.update_experience(other.id, exp.id, {"company": "Apple"})

    # ── Skills ──

    async def test_add_skill_with_level(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        skill = await service.add_skill(user.id, {"name": "Python", "skill_level": "advanced", "display_order": 1})
        assert skill.skill_level == "advanced"
        assert skill.display_order == 1

    async def test_add_duplicate_skill_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_skill(user.id, {"name": "Python"})
        with pytest.raises(ConflictError, match="Duplicate skill"):
            await service.add_skill(user.id, {"name": "python"})

    async def test_add_empty_skill_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        with pytest.raises(ValidationError, match="Skill name is required"):
            await service.add_skill(user.id, {"name": "   "})

    async def test_update_skill_duplicate_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_skill(user.id, {"name": "Python"})
        sql = await service.add_skill(user.id, {"name": "SQL"})
        with pytest.raises(ConflictError):
            await service.update_skill(user.id, sql.id, {"name": "python"})

    async def test_replace_skills_replaces_existing_list(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_skill(user.id, {"name": "Python"})
        await service.add_skill(user.id, {"name": "Old Skill"})
        replaced = await service.replace_skills(user.id, ["FastAPI", "Docker"])
        assert {s.name for s in replaced} == {"FastAPI", "Docker"}
        profile = await service.get_profile(user.id)
        assert [s.name for s in profile.skills] == ["Docker", "FastAPI"]

    async def test_replace_skills_dedupes_case_insensitively(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        replaced = await service.replace_skills(user.id, ["Python", "python", "PYTHON", "SQL"])
        assert [s.name for s in replaced] == ["Python", "SQL"]

    async def test_replace_skills_trims_and_skips_empty_names(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        replaced = await service.replace_skills(user.id, ["  Python  ", "", "   ", "SQL"])
        assert [s.name for s in replaced] == ["Python", "SQL"]
        profile = await service.get_profile(user.id)
        assert [s.name for s in profile.skills] == ["Python", "SQL"]

    async def test_replace_skills_empty_list_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        with pytest.raises(ValidationError, match="Skill name is required"):
            await service.replace_skills(user.id, ["   "])

    async def test_replace_skills_recomputes_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.replace_skills(user.id, ["Python", "SQL", "Docker"])
        profile = await service.get_profile(user.id)
        assert profile.profile_completeness >= 0

    # ── Projects ──

    async def test_add_project_with_dates(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        proj = await service.add_project(
            user.id,
            {
                "name": "Portfolio",
                "live_url": "https://example.com",
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 6, 1),
            },
        )
        assert proj.live_url == "https://example.com"

    async def test_add_duplicate_project_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_project(user.id, {"name": "Portfolio"})
        with pytest.raises(ConflictError, match="Duplicate project"):
            await service.add_project(user.id, {"name": "portfolio"})

    # ── Certifications ──

    async def test_add_certification(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        cert = await service.add_certification(
            user.id,
            {
                "name": "AWS",
                "issuer": "Amazon",
                "credential_id": "AWS-123",
                "issue_date": date(2024, 1, 1),
                "expiration_date": date(2025, 1, 1),
                "credential_url": "https://credential.com/aws-123",
            },
        )
        assert cert.credential_id == "AWS-123"

    async def test_add_duplicate_certification_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_certification(user.id, {"name": "AWS"})
        with pytest.raises(ConflictError, match="Duplicate certification"):
            await service.add_certification(user.id, {"name": "aws"})

    # ── Languages ──

    async def test_add_language(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        lang = await service.add_language(user.id, {"language": "english", "proficiency": "Native"})
        assert lang.language == "English"
        assert lang.proficiency == "Native"

    async def test_add_duplicate_language_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_language(user.id, {"language": "English"})
        with pytest.raises(ConflictError, match="Duplicate language"):
            await service.add_language(user.id, {"language": "english"})

    async def test_update_language_duplicate_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_language(user.id, {"language": "English"})
        spanish = await service.add_language(user.id, {"language": "Spanish"})
        with pytest.raises(ConflictError):
            await service.update_language(user.id, spanish.id, {"language": "english"})

    # ── Achievements ──

    async def test_add_achievement(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        achievement = await service.add_achievement(
            user.id,
            {
                "title": "Hackathon Winner",
                "organization": "TechConf",
                "achievement_type": "Hackathon Winner",
                "date": date(2026, 3, 1),
                "description": "Won first place among 200 teams",
                "url": "https://example.com/hackathon",
            },
        )
        assert achievement.title == "Hackathon Winner"
        assert achievement.organization == "TechConf"

    async def test_add_duplicate_achievement_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_achievement(user.id, {"title": "Hackathon Winner"})
        with pytest.raises(ConflictError, match="Duplicate achievement"):
            await service.add_achievement(user.id, {"title": "hackathon winner"})

    async def test_add_empty_achievement_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        with pytest.raises(ValidationError, match="Achievement title is required"):
            await service.add_achievement(user.id, {"title": ""})

    async def test_update_achievement(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        achievement = await service.add_achievement(user.id, {"title": "Award"})
        updated = await service.update_achievement(user.id, achievement.id, {"organization": "Acme"})
        assert updated.organization == "Acme"

    async def test_update_achievement_ownership(self, db_session):
        user = await _create_user(db_session)
        other = await _create_user(db_session, "other_ach@test.com")
        service = CareerProfileService(db_session)
        achievement = await service.add_achievement(user.id, {"title": "Award"})
        with pytest.raises(NotFoundError):
            await service.update_achievement(other.id, achievement.id, {"title": "X"})

    async def test_delete_achievement_updates_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        achievement = await service.add_achievement(user.id, {"title": "Award"})
        before = await service.calculate_completeness(user.id)
        assert before["breakdown"]["achievements"] == 5
        await service.delete_achievement(user.id, achievement.id)
        after = await service.calculate_completeness(user.id)
        assert after["breakdown"]["achievements"] == 0

    # ── Social Links ──

    async def test_add_social_link(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "GitHub", "url": "https://github.com/test"})
        assert link.platform == "github"
        assert link.profile_id is not None

    async def test_add_duplicate_social_link_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_social_link(user.id, {"platform": "github", "url": "https://github.com/a"})
        with pytest.raises(ConflictError, match="Duplicate social link"):
            await service.add_social_link(user.id, {"platform": "GitHub", "url": "https://github.com/b"})

    async def test_update_social_link_ownership(self, db_session):
        user = await _create_user(db_session)
        other = await _create_user(db_session, "other3@test.com")
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "github", "url": "https://github.com/test"})
        with pytest.raises(NotFoundError):
            await service.update_social_link(other.id, link.id, {"platform": "portfolio"})

    async def test_delete_social_link(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "github", "url": "https://github.com/test"})
        await service.delete_social_link(user.id, link.id)
        link_repo = SocialLinkRepository(db_session)
        deleted = await link_repo.get_by_id(link.id)
        assert deleted is None

    async def test_delete_others_social_link_raises(self, db_session):
        user = await _create_user(db_session)
        other = await _create_user(db_session, "other4@test.com")
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "github", "url": "https://github.com/test"})
        with pytest.raises(NotFoundError):
            await service.delete_social_link(other.id, link.id)

    # ── Profile Completeness ──

    async def test_empty_profile_completeness_is_zero(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        result = await service.calculate_completeness(user.id)
        assert result["percentage"] == 0
        assert "headline" in result["missing_sections"]
        assert "education" in result["missing_sections"]
        assert "achievements" in result["missing_sections"]

    async def test_completeness_never_exceeds_100(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        result = await service.calculate_completeness(user.id)
        assert 0 <= result["percentage"] <= 100
        for value in result["breakdown"].values():
            assert value >= 0

    async def test_partial_profile_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        await service.add_experience(user.id, {"company": "Google", "title": "Engineer"})
        await service.add_skill(user.id, {"name": "Python"})
        await service.add_project(user.id, {"name": "My Project"})
        await service.update_profile(user.id, {"headline": "Dev", "professional_summary": "A summary"})
        result = await service.calculate_completeness(user.id)
        assert result["percentage"] > 0
        assert "education" not in result["missing_sections"]
        assert "experience" not in result["missing_sections"]
        assert "languages" in result["missing_sections"]
        assert "achievements" in result["missing_sections"]

    async def test_achievements_contribute_to_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        result = await service.calculate_completeness(user.id)
        assert result["breakdown"]["achievements"] == 0
        await service.add_achievement(user.id, {"title": "Award"})
        result = await service.calculate_completeness(user.id)
        assert result["breakdown"]["achievements"] == 5

    async def test_social_links_contribute_to_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        result = await service.calculate_completeness(user.id)
        assert result["breakdown"]["social_links"] == 0
        await service.add_social_link(user.id, {"platform": "github", "url": "https://github.com/a"})
        result = await service.calculate_completeness(user.id)
        assert result["breakdown"]["social_links"] == 5

    async def test_salary_preference_contributes_to_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        result = await service.calculate_completeness(user.id)
        assert result["breakdown"]["salary_preference"] == 0
        await service.update_profile(user.id, {"salary_preference": "paid_preferred"})
        result = await service.calculate_completeness(user.id)
        assert result["breakdown"]["salary_preference"] == 3

    async def test_full_profile_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.update_profile(
            user.id,
            {
                "headline": "Dev",
                "professional_summary": "Summary",
                "total_years_experience": 5,
                "current_role": "E",
                "desired_role": "L",
                "employment_status": "employed",
                "current_salary": 100,
                "expected_salary": 130,
                "salary_preference": "paid_only",
                "willing_to_relocate": True,
                "notice_period": "2w",
                "portfolio_url": "https://p.com",
                "linkedin_url": "https://l.com",
                "github_url": "https://g.com",
                "website_url": "https://w.com",
            },
        )
        await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        await service.add_experience(user.id, {"company": "G", "title": "E"})
        await service.add_skill(user.id, {"name": "Python"})
        await service.add_project(user.id, {"name": "P"})
        await service.add_certification(user.id, {"name": "AWS"})
        await service.add_language(user.id, {"language": "English", "proficiency": "Native"})
        await service.add_achievement(user.id, {"title": "Award", "organization": "Acme"})
        await service.add_social_link(user.id, {"platform": "github", "url": "https://github.com/a"})
        result = await service.calculate_completeness(user.id)
        assert result["percentage"] == 100
        assert len(result["missing_sections"]) == 0

    # ── Delete Operations ──

    async def test_delete_certification_updates_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        cert = await service.add_certification(user.id, {"name": "AWS"})
        before = await service.calculate_completeness(user.id)
        assert before["breakdown"]["certifications"] == 4
        await service.delete_certification(user.id, cert.id)
        after = await service.calculate_completeness(user.id)
        assert after["breakdown"]["certifications"] == 0

    async def test_delete_nonexistent_entity_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        fake_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await service.delete_education(user.id, fake_id)
        with pytest.raises(NotFoundError):
            await service.delete_experience(user.id, fake_id)
        with pytest.raises(NotFoundError):
            await service.delete_skill(user.id, fake_id)
        with pytest.raises(NotFoundError):
            await service.delete_project(user.id, fake_id)
        with pytest.raises(NotFoundError):
            await service.delete_certification(user.id, fake_id)
        with pytest.raises(NotFoundError):
            await service.delete_language(user.id, fake_id)
        with pytest.raises(NotFoundError):
            await service.delete_social_link(user.id, fake_id)
        with pytest.raises(NotFoundError):
            await service.delete_achievement(user.id, fake_id)

    async def test_update_nonexistent_entity_raises(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        fake_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await service.update_education(user.id, fake_id, {"institution": "X"})
        with pytest.raises(NotFoundError):
            await service.update_experience(user.id, fake_id, {"company": "X"})
        with pytest.raises(NotFoundError):
            await service.update_skill(user.id, fake_id, {"name": "X"})
        with pytest.raises(NotFoundError):
            await service.update_project(user.id, fake_id, {"name": "X"})
        with pytest.raises(NotFoundError):
            await service.update_certification(user.id, fake_id, {"name": "X"})
        with pytest.raises(NotFoundError):
            await service.update_language(user.id, fake_id, {"language": "X"})
        with pytest.raises(NotFoundError):
            await service.update_social_link(user.id, fake_id, {"platform": "X"})
        with pytest.raises(NotFoundError):
            await service.update_achievement(user.id, fake_id, {"title": "X"})

    # ── Profile Completeness Auto-Update ──

    async def test_completeness_updates_on_add(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        profile = await service.get_profile(user.id)
        assert profile.profile_completeness is not None

    async def test_completeness_updates_on_delete(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        profile = await service.get_profile(user.id)
        initial = profile.profile_completeness
        await service.delete_education(user.id, edu.id)
        profile = await service.get_profile(user.id)
        final = profile.profile_completeness
        assert final < initial


# ── API Tests ──


class TestCareerProfileAPI:
    @pytest_asyncio.fixture
    async def api_client(self, db_session: AsyncSession):
        app = FastAPI()

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        @app.exception_handler(NotFoundError)
        async def not_found_handler(request, exc):
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.message})

        @app.exception_handler(ValidationError)
        async def validation_handler(request, exc):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.message})

        @app.exception_handler(AuthenticationError)
        async def auth_error_handler(request, exc):
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": exc.message})

        @app.exception_handler(ConflictError)
        async def conflict_handler(request, exc):
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": exc.message})

        app.include_router(profile_router, prefix="/profile")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def _auth_headers(self, db_session, user_id: uuid.UUID) -> dict:
        token = create_access_token(subject=str(user_id))
        return {"Authorization": f"Bearer {token}"}

    async def test_get_profile_unauthenticated(self, api_client):
        resp = await api_client.get("/profile/")
        assert resp.status_code in (401, 403)

    async def test_get_profile_authenticated(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.get("/profile/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "headline" in data["data"]
        assert "salary_preference" in data["data"]
        assert "achievements" in data["data"]

    async def test_update_profile(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.patch("/profile/", json={"headline": "Senior Dev"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["headline"] == "Senior Dev"

    async def test_update_profile_salary_preference(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.patch(
            "/profile/",
            json={"salary_preference": "paid_preferred", "expected_salary": 90000},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["salary_preference"] == "paid_preferred"

    async def test_update_profile_invalid_salary_preference(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.patch("/profile/", json={"salary_preference": "bogus"}, headers=headers)
        assert resp.status_code == 422

    async def test_completeness_empty(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.get("/profile/completeness", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["percentage"] == 0
        assert data["data"]["percentage"] is not None

    async def test_completeness_with_data(self, api_client, db_session):
        user = await _create_user(db_session)
        await _create_full_profile(db_session, user.id)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.get("/profile/completeness", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["percentage"] > 0
        assert "achievements" in data["data"]["breakdown"]
        assert "social_links" in data["data"]["breakdown"]
        assert "salary_preference" in data["data"]["breakdown"]

    # ── Education API ──

    async def test_add_education_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/education",
            json={"institution": "MIT", "degree": "BS", "location": "Cambridge, MA"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["institution"] == "MIT"
        assert data["data"]["location"] == "Cambridge, MA"
        assert "description" not in data["data"]

    async def test_add_education_invalid_dates_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/education",
            json={
                "institution": "MIT",
                "degree": "BS",
                "start_date": "2024-06-01",
                "end_date": "2024-01-01",
            },
            headers=headers,
        )
        assert resp.status_code == 422

    async def test_update_education_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.patch(
            f"/profile/education/{edu.id}",
            json={"institution": "Stanford"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["institution"] == "Stanford"

    async def test_delete_education_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.delete(f"/profile/education/{edu.id}", headers=headers)
        assert resp.status_code == 204

    # ── Experience API ──

    async def test_add_experience_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/experience",
            json={"company": "Google", "title": "Engineer"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["company"] == "Google"

    async def test_add_experience_current_job_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/experience",
            json={"company": "Google", "title": "Engineer", "currently_working": True, "end_date": "2024-06-01"},
            headers=headers,
        )
        assert resp.status_code == 422

    # ── Skills API ──

    async def test_add_skill_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/skills",
            json={"name": "Python", "skill_level": "advanced"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["skill_level"] == "advanced"

    async def test_add_duplicate_skill_api_returns_409(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post("/profile/skills", json={"name": "Python"}, headers=headers)
        assert resp.status_code == 201
        resp = await api_client.post("/profile/skills", json={"name": "Python"}, headers=headers)
        assert resp.status_code == 409
        assert "Duplicate skill" in resp.json()["detail"]

    async def test_replace_skills_api_replaces_whole_list(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post("/profile/skills", json={"name": "Python"}, headers=headers)
        assert resp.status_code == 201
        resp = await api_client.put(
            "/profile/skills",
            json={"skills": ["FastAPI", "Docker", "PostgreSQL"]},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert [s["name"] for s in data] == ["Docker", "FastAPI", "PostgreSQL"]
        resp = await api_client.get("/profile/skills", headers=headers)
        assert resp.status_code == 200
        assert [s["name"] for s in resp.json()["data"]] == ["Docker", "FastAPI", "PostgreSQL"]

    async def test_replace_skills_api_dedupes_case_insensitively(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.put(
            "/profile/skills",
            json={"skills": ["Python", "python", "SQL"]},
            headers=headers,
        )
        assert resp.status_code == 200
        assert [s["name"] for s in resp.json()["data"]] == ["Python", "SQL"]

    async def test_replace_skills_api_rejects_empty_list(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.put("/profile/skills", json={"skills": []}, headers=headers)
        assert resp.status_code == 422
        resp = await api_client.put("/profile/skills", json={"skills": ["  "]}, headers=headers)
        assert resp.status_code == 422

    # ── Projects API ──

    async def test_add_project_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/projects",
            json={"name": "Portfolio", "live_url": "https://example.com"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["live_url"] == "https://example.com"

    async def test_add_project_invalid_url_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/projects",
            json={"name": "Portfolio", "github_url": "example.com/bad"},
            headers=headers,
        )
        assert resp.status_code == 422

    # ── Certifications API ──

    async def test_add_certification_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/certifications",
            json={"name": "AWS Solutions Architect"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "AWS Solutions Architect"

    async def test_add_duplicate_certification_api_returns_409(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post("/profile/certifications", json={"name": "AWS"}, headers=headers)
        assert resp.status_code == 201
        resp = await api_client.post("/profile/certifications", json={"name": "aws"}, headers=headers)
        assert resp.status_code == 409

    # ── Languages API ──

    async def test_add_language_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/languages",
            json={"language": "English", "proficiency": "Native"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["language"] == "English"

    async def test_update_language_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        lang = await service.add_language(user.id, {"language": "English"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.patch(
            f"/profile/languages/{lang.id}",
            json={"proficiency": "Fluent"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["proficiency"] == "Fluent"

    async def test_add_duplicate_language_api_returns_409(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/languages",
            json={"language": "English", "proficiency": "Native"},
            headers=headers,
        )
        assert resp.status_code == 201
        resp = await api_client.post(
            "/profile/languages",
            json={"language": "english", "proficiency": "Beginner"},
            headers=headers,
        )
        assert resp.status_code == 409
        assert "Duplicate language" in resp.json()["detail"]

    # ── Achievements API ──

    async def test_add_achievement_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/achievements",
            json={
                "title": "Hackathon Winner",
                "organization": "TechConf",
                "achievement_type": "Hackathon Winner",
                "date": "2026-03-01",
                "description": "Won first place",
                "url": "https://example.com/award",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "Hackathon Winner"
        assert data["organization"] == "TechConf"

    async def test_list_achievements_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        await service.add_achievement(user.id, {"title": "Award"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.get("/profile/achievements", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["title"] == "Award"

    async def test_update_achievement_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        achievement = await service.add_achievement(user.id, {"title": "Award"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.patch(
            f"/profile/achievements/{achievement.id}",
            json={"organization": "Acme"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["organization"] == "Acme"

    async def test_delete_achievement_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        achievement = await service.add_achievement(user.id, {"title": "Award"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.delete(f"/profile/achievements/{achievement.id}", headers=headers)
        assert resp.status_code == 204

    async def test_add_duplicate_achievement_api_returns_409(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post("/profile/achievements", json={"title": "Award"}, headers=headers)
        assert resp.status_code == 201
        resp = await api_client.post("/profile/achievements", json={"title": "award"}, headers=headers)
        assert resp.status_code == 409
        assert "Duplicate achievement" in resp.json()["detail"]

    async def test_add_achievement_invalid_url_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/achievements",
            json={"title": "Award", "url": "not-a-url"},
            headers=headers,
        )
        assert resp.status_code == 422

    # ── Social Links API ──

    async def test_add_social_link_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/social-links",
            json={"platform": "GitHub", "url": "https://github.com/test"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["platform"] == "github"
        assert data["title"] == "GitHub"

    async def test_update_social_link_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "github", "url": "https://github.com/test"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.patch(
            f"/profile/social-links/{link.id}",
            json={"platform": "portfolio"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["platform"] == "portfolio"
        assert resp.json()["data"]["title"] == "Portfolio"

    async def test_delete_social_link_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "github", "url": "https://github.com/test"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.delete(f"/profile/social-links/{link.id}", headers=headers)
        assert resp.status_code == 204

    async def test_social_link_requires_auth(self, api_client):
        resp = await api_client.post(
            "/profile/social-links",
            json={"platform": "github", "url": "https://github.com/test"},
        )
        assert resp.status_code in (401, 403)

    async def test_add_duplicate_social_link_api_returns_409(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/social-links",
            json={"platform": "github", "url": "https://github.com/a"},
            headers=headers,
        )
        assert resp.status_code == 201
        resp = await api_client.post(
            "/profile/social-links",
            json={"platform": "GitHub", "url": "https://github.com/b"},
            headers=headers,
        )
        assert resp.status_code == 409

    async def test_legacy_social_link_rows_do_not_crash_profile_routes(self, api_client, db_session):
        """Legacy rows (pre-enum) with unknown/cased platforms must never 500 the profile routes."""
        await db_session.execute(
            text("ALTER TABLE social_links DROP CONSTRAINT IF EXISTS ck_social_link_platform")
        )
        await db_session.commit()
        try:
            user = await _create_user(db_session)
            profile = await _create_profile(db_session, user.id)
            db_session.add_all([
                SocialLink(profile_id=profile.id, platform="sq", url="https://legacy.example.com"),
                SocialLink(profile_id=profile.id, platform="LinkedIn", url="https://www.linkedin.com/in/legacy"),
            ])
            await db_session.commit()
            headers = await self._auth_headers(db_session, user.id)

            resp = await api_client.get("/profile/social-links", headers=headers)
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert {link["platform"] for link in data} == {"linkedin", "other"}

            resp = await api_client.get("/profile", headers=headers)
            assert resp.status_code == 200
            assert "social_links" in resp.json()["data"]

            resp = await api_client.patch("/profile", json={"headline": "Legacy Safe"}, headers=headers)
            assert resp.status_code == 200
            assert resp.json()["data"]["headline"] == "Legacy Safe"
        finally:
            await db_session.execute(text("DELETE FROM social_links"))
            await db_session.commit()
            await db_session.execute(
                text(
                    "ALTER TABLE social_links ADD CONSTRAINT ck_social_link_platform "
                    "CHECK (platform IN ('linkedin', 'github', 'portfolio', 'website', 'other'))"
                )
            )
            await db_session.commit()

    async def test_social_link_model_rejects_invalid_platform(self, db_session):
        user = await _create_user(db_session)
        profile = await _create_profile(db_session, user.id)
        db_session.add(SocialLink(profile_id=profile.id, platform="sq", url="https://legacy.example.com"))
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    async def test_social_link_response_coerces_unknown_platform(self):
        from datetime import datetime, timezone

        link = SocialLinkResponse(
            id=uuid.uuid4(),
            profile_id=uuid.uuid4(),
            platform="sq",
            url="https://legacy.example.com",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert link.platform == "other"
        assert link.title == "Other"

    async def test_social_link_response_normalizes_cased_platform(self):
        from datetime import datetime, timezone

        link = SocialLinkResponse(
            id=uuid.uuid4(),
            profile_id=uuid.uuid4(),
            platform="  LinkedIn ",
            url="https://www.linkedin.com/in/x",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert link.platform == "linkedin"
        assert link.title == "LinkedIn"

    async def test_other_users_cannot_modify_education(self, api_client, db_session):
        user = await _create_user(db_session)
        other = await _create_user(db_session, "other_api@test.com")
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, other.id)
        resp = await api_client.patch(f"/profile/education/{edu.id}", json={"institution": "X"}, headers=headers)
        assert resp.status_code == 404
