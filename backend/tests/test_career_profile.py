import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.profile import router as profile_router
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import create_access_token, get_password_hash
from app.schemas.career_profile import CareerProfileUpdate
from app.schemas.social_link import SocialLinkCreate
from app.services.profile import CareerProfileService
from database.models.career_profile import CareerProfile
from database.models.education import Education
from database.models.experience import Experience
from database.models.project import Project
from database.models.skill import Skill
from database.models.social_link import SocialLink
from database.models.user import User
from database.repositories import (
    CareerProfileRepository,
    EducationRepository,
    ExperienceRepository,
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
            willing_to_relocate=True,
            visa_sponsorship_requirement=False,
            notice_period="2 weeks",
        )
        session.add(profile)
        await session.flush()
        assert profile.headline == "Senior Developer"
        assert profile.total_years_experience == 8.5
        assert profile.current_role == "Senior Engineer"
        assert profile.desired_role == "Lead Developer"

    async def test_default_profile_completeness(self, session):
        user = await _create_user(session)
        profile = CareerProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
        assert profile.profile_completeness == 0


class TestSocialLinkModel:
    async def test_create_social_link(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        link = SocialLink(profile_id=profile.id, platform="GitHub", url="https://github.com/test")
        session.add(link)
        await session.flush()
        assert link.id is not None
        assert link.platform == "GitHub"

    async def test_cascade_delete(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        link = SocialLink(profile_id=profile.id, platform="LinkedIn", url="https://linkedin.com/in/test")
        session.add(link)
        await session.flush()
        link_id = link.id
        await session.delete(profile)
        await session.flush()
        deleted = await session.get(SocialLink, link_id)
        assert deleted is None


class TestEducationNewFields:
    async def test_currently_studying(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        edu = Education(profile_id=profile.id, institution="MIT", degree="BS", currently_studying=True)
        session.add(edu)
        await session.flush()
        assert edu.currently_studying is True


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
        from datetime import date

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


class TestSocialLinkRepository:
    async def test_list_by_profile(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        repo = SocialLinkRepository(session)
        link1 = SocialLink(profile_id=profile.id, platform="GitHub", url="https://github.com/a", display_order=2)
        link2 = SocialLink(profile_id=profile.id, platform="LinkedIn", url="https://linkedin.com/in/a", display_order=1)
        await repo.create(link1)
        await repo.create(link2)
        links = await repo.list_by_profile(profile.id)
        assert len(links) == 2
        assert links[0].platform == "LinkedIn"
        assert links[1].platform == "GitHub"

    async def test_exists_by_platform(self, session):
        user = await _create_user(session)
        profile = await _create_profile(session, user.id)
        repo = SocialLinkRepository(session)
        link = SocialLink(profile_id=profile.id, platform="GitHub", url="https://github.com/a")
        await repo.create(link)
        assert await repo.exists_by_platform(profile.id, "GitHub") is True
        assert await repo.exists_by_platform(profile.id, "Twitter") is False


# ── Schema Validation Tests ──


class TestSocialLinkValidation:
    def test_valid_url(self):
        link = SocialLinkCreate(platform="GitHub", url="https://github.com/test")
        assert link.url == "https://github.com/test"

    def test_invalid_url(self):
        with pytest.raises(ValueError, match="URL must start with"):
            SocialLinkCreate(platform="GitHub", url="ftp://invalid.com")

    def test_invalid_url_no_scheme(self):
        with pytest.raises(ValueError, match="URL must start with"):
            SocialLinkCreate(platform="GitHub", url="github.com/test")


class TestCareerProfileUpdateValidation:
    def test_valid_urls(self):
        data = CareerProfileUpdate(linkedin_url="https://linkedin.com/in/test")
        assert data.linkedin_url == "https://linkedin.com/in/test"

    def test_invalid_urls(self):
        with pytest.raises(ValueError, match="URL must start with"):
            CareerProfileUpdate(portfolio_url="not-a-url")

    def test_total_years_experience_range(self):
        with pytest.raises(ValueError):
            CareerProfileUpdate(total_years_experience=-1)


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

    # ── Education ──

    async def test_add_education(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS", "field_of_study": "CS"})
        assert edu.id is not None
        assert edu.institution == "MIT"
        assert edu.currently_studying is False

    async def test_add_education_with_currently_studying(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS", "currently_studying": True})
        assert edu.currently_studying is True

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
        assert completeness["breakdown"]["education"] == 10
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

    # ── Projects ──

    async def test_add_project_with_dates(self, db_session):
        from datetime import date

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

    # ── Social Links ──

    async def test_add_social_link(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "GitHub", "url": "https://github.com/test"})
        assert link.platform == "GitHub"
        assert link.profile_id is not None

    async def test_update_social_link_ownership(self, db_session):
        user = await _create_user(db_session)
        other = await _create_user(db_session, "other3@test.com")
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "GitHub", "url": "https://github.com/test"})
        with pytest.raises(NotFoundError):
            await service.update_social_link(other.id, link.id, {"platform": "GitLab"})

    async def test_delete_social_link(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "GitHub", "url": "https://github.com/test"})
        await service.delete_social_link(user.id, link.id)
        link_repo = SocialLinkRepository(db_session)
        deleted = await link_repo.get_by_id(link.id)
        assert deleted is None

    async def test_delete_others_social_link_raises(self, db_session):
        user = await _create_user(db_session)
        other = await _create_user(db_session, "other4@test.com")
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "GitHub", "url": "https://github.com/test"})
        with pytest.raises(NotFoundError):
            await service.delete_social_link(other.id, link.id)

    # ── Profile Completeness ──

    async def test_empty_profile_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        result = await service.calculate_completeness(user.id)
        assert result["percentage"] == 0
        assert len(result["missing_sections"]) == 20
        assert "headline" in result["missing_sections"]
        assert "education" in result["missing_sections"]

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
        result = await service.calculate_completeness(user.id)
        assert result["percentage"] == 100
        assert len(result["missing_sections"]) == 0

    # ── Delete Operations ──

    async def test_delete_certification_updates_completeness(self, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        cert = await service.add_certification(user.id, {"name": "AWS"})
        before = await service.calculate_completeness(user.id)
        assert before["breakdown"]["certifications"] == 5
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

    async def test_update_profile(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.patch("/profile/", json={"headline": "Senior Dev"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["headline"] == "Senior Dev"

    async def test_completeness_empty(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.get("/profile/completeness", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["percentage"] == 0

    async def test_completeness_with_data(self, api_client, db_session):
        user = await _create_user(db_session)
        await _create_full_profile(db_session, user.id)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.get("/profile/completeness", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["percentage"] > 0

    # ── Education API ──

    async def test_add_education_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await db_session.commit()
        resp = await api_client.post(
            "/profile/education",
            json={"institution": "MIT", "degree": "BS"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["institution"] == "MIT"

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
        assert resp.json()["data"]["platform"] == "GitHub"

    async def test_update_social_link_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "GitHub", "url": "https://github.com/test"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.patch(
            f"/profile/social-links/{link.id}",
            json={"platform": "GitLab"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["platform"] == "GitLab"

    async def test_delete_social_link_api(self, api_client, db_session):
        user = await _create_user(db_session)
        service = CareerProfileService(db_session)
        link = await service.add_social_link(user.id, {"platform": "GitHub", "url": "https://github.com/test"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.delete(f"/profile/social-links/{link.id}", headers=headers)
        assert resp.status_code == 204

    async def test_social_link_requires_auth(self, api_client):
        resp = await api_client.post(
            "/profile/social-links",
            json={"platform": "GitHub", "url": "https://github.com/test"},
        )
        assert resp.status_code in (401, 403)

    async def test_other_users_cannot_modify_education(self, api_client, db_session):
        user = await _create_user(db_session)
        other = await _create_user(db_session, "other_api@test.com")
        service = CareerProfileService(db_session)
        edu = await service.add_education(user.id, {"institution": "MIT", "degree": "BS"})
        await db_session.commit()
        headers = await self._auth_headers(db_session, other.id)
        resp = await api_client.patch(f"/profile/education/{edu.id}", json={"institution": "X"}, headers=headers)
        assert resp.status_code == 404
