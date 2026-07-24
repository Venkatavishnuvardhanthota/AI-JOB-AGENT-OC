import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.resumes import router as resumes_router
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import create_access_token, get_password_hash
from app.schemas.resume import (
    ResumeImportData,
    ResumeSectionCreate,
)
from app.services.resume import ResumeService
from database.models.resume_section import ResumeSection
from database.models.resume_version import ResumeVersion
from database.models.user import User
from database.repositories import ResumeVersionRepository, UserRepository


async def _create_user(session: AsyncSession, email: str = "resume@test.com") -> User:
    repo = UserRepository(session)
    user = User(
        email=email,
        password_hash=get_password_hash("TestPass123!"),
        first_name="Test",
        last_name="User",
    )
    return await repo.create(user)


# ── Model Tests ──


class TestResumeVersionModel:
    async def test_create_with_new_fields(self, session):
        user = User(email="rvnew@test.com", password_hash="h", first_name="R", last_name="V")
        session.add(user)
        await session.flush()
        rv = ResumeVersion(
            user_id=user.id,
            version=1,
            title="My Resume",
            description="A test resume",
            status="draft",
            source="manual",
            resume_type="professional",
            is_default=True,
            change_summary="Initial version",
        )
        session.add(rv)
        await session.flush()
        assert rv.id is not None
        assert rv.version == 1
        assert rv.title == "My Resume"
        assert rv.description == "A test resume"
        assert rv.status == "draft"
        assert rv.source == "manual"
        assert rv.resume_type == "professional"
        assert rv.is_default is True
        assert rv.change_summary == "Initial version"
        assert rv.archived is False

    async def test_resume_version_ordering(self, session):
        user = User(email="rvord@test.com", password_hash="h", first_name="R", last_name="O")
        session.add(user)
        await session.flush()
        rv1 = ResumeVersion(user_id=user.id, version=1)
        session.add(rv1)
        await session.flush()
        rv2 = ResumeVersion(user_id=user.id, version=2, previous_version_id=rv1.id)
        session.add(rv2)
        await session.flush()
        assert rv2.previous_version_id == rv1.id


class TestResumeSectionModel:
    async def test_create_section(self, session):
        user = User(email="rsect@test.com", password_hash="h", first_name="R", last_name="S")
        session.add(user)
        await session.flush()
        rv = ResumeVersion(user_id=user.id, version=1)
        session.add(rv)
        await session.flush()
        section = ResumeSection(
            resume_id=rv.id,
            section_type="education",
            title="Education",
            content={"school": "MIT"},
            sort_order=1,
            visible=True,
        )
        session.add(section)
        await session.flush()
        assert section.id is not None
        assert section.section_type == "education"
        assert section.sort_order == 1
        assert section.visible is True

    async def test_section_cascade_delete(self, session):
        user = User(email="rsccd@test.com", password_hash="h", first_name="R", last_name="C")
        session.add(user)
        await session.flush()
        rv = ResumeVersion(user_id=user.id, version=1)
        session.add(rv)
        await session.flush()
        section = ResumeSection(resume_id=rv.id, section_type="summary")
        session.add(section)
        await session.flush()
        section_id = section.id
        await session.delete(rv)
        await session.flush()
        result = await session.get(ResumeSection, section_id)
        assert result is None


# ── Repository Tests ──


@pytest.mark.usefixtures("session")
class TestResumeVersionRepository:
    async def test_list_by_user_with_sections(self, session):
        user = await UserRepository(session).create(
            User(email="rvws@test.com", password_hash="h", first_name="R", last_name="W")
        )
        repo = ResumeVersionRepository(session)
        rv = await repo.create(ResumeVersion(user_id=user.id, version=1))
        section = ResumeSection(resume_id=rv.id, section_type="summary")
        await repo.session.add(section)
        await repo.session.flush()
        results = await repo.list_by_user_with_sections(user.id)
        assert len(results) == 1
        assert len(results[0].sections) == 1

    async def test_get_with_sections(self, session):
        user = await UserRepository(session).create(
            User(email="rvgws@test.com", password_hash="h", first_name="R", last_name="G")
        )
        repo = ResumeVersionRepository(session)
        rv = await repo.create(ResumeVersion(user_id=user.id, version=1))
        section = ResumeSection(resume_id=rv.id, section_type="experience")
        await repo.session.add(section)
        await repo.session.flush()
        loaded = await repo.get_with_sections(rv.id)
        assert loaded is not None
        assert len(loaded.sections) == 1

    async def test_set_and_get_default(self, session):
        user = await UserRepository(session).create(
            User(email="rvdef@test.com", password_hash="h", first_name="R", last_name="D")
        )
        repo = ResumeVersionRepository(session)
        await repo.create(ResumeVersion(user_id=user.id, version=1))
        rv2 = await repo.create(ResumeVersion(user_id=user.id, version=2))
        await repo.set_default(rv2.id, user.id)
        default = await repo.get_default(user.id)
        assert default is not None
        assert default.id == rv2.id
        assert default.is_default is True
        await repo.unset_default(user.id)
        default = await repo.get_default(user.id)
        assert default is None


@pytest.mark.usefixtures("session")
class TestResumeSectionRepository:
    async def test_list_by_resume(self, session):
        from database.repositories import ResumeSectionRepository as SectionRepo

        user = await UserRepository(session).create(
            User(email="slist@test.com", password_hash="h", first_name="S", last_name="L")
        )
        repo = ResumeVersionRepository(session)
        rv = await repo.create(ResumeVersion(user_id=user.id, version=1))
        section_repo = SectionRepo(session)
        for section_type in ["summary", "education", "experience"]:
            s = ResumeSection(resume_id=rv.id, section_type=section_type, sort_order=0)
            await section_repo.create(s)
        sections = await section_repo.list_by_resume(rv.id)
        assert len(sections) == 3

    async def test_delete_all_for_resume(self, session):
        from database.repositories import ResumeSectionRepository as SectionRepo

        user = await UserRepository(session).create(
            User(email="sdel@test.com", password_hash="h", first_name="S", last_name="D")
        )
        repo = ResumeVersionRepository(session)
        rv = await repo.create(ResumeVersion(user_id=user.id, version=1))
        section_repo = SectionRepo(session)
        section = ResumeSection(resume_id=rv.id, section_type="summary")
        await section_repo.create(section)
        await section_repo.delete_all_for_resume(rv.id)
        remaining = await section_repo.list_by_resume(rv.id)
        assert len(remaining) == 0


# ── Service Tests ──


class TestResumeService:
    async def test_create_resume(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        resume = await service.create_resume(user.id, title="My Resume", description="Test")
        assert resume.id is not None
        assert resume.title == "My Resume"
        assert resume.description == "Test"
        assert resume.version == 1
        assert resume.status == "draft"
        assert resume.source == "manual"
        assert resume.is_default is True

    async def test_create_resume_with_sections(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        sections = [
            {"section_type": "summary", "title": "Summary", "content": {"text": "Experienced developer"}},
            {"section_type": "education", "title": "Education", "sort_order": 1},
        ]
        resume = await service.create_resume(
            user.id,
            title="With Sections",
            sections=sections,
        )
        assert len(resume.sections) == 2
        assert resume.sections[0].section_type == "summary"

    async def test_list_resumes(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        await service.create_resume(user.id, title="Resume 1")
        await service.create_resume(user.id, title="Resume 2")
        resumes = await service.list_resumes(user.id)
        assert len(resumes) == 2

    async def test_get_resume(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        created = await service.create_resume(user.id, title="Get Me")
        fetched = await service.get_resume(created.id, user.id)
        assert fetched.id == created.id
        assert fetched.title == "Get Me"

    async def test_get_resume_wrong_user(self, db_session):
        user1 = await _create_user(db_session, "user1@test.com")
        user2 = await _create_user(db_session, "user2@test.com")
        service = ResumeService(db_session)
        created = await service.create_resume(user1.id, title="Mine")
        with pytest.raises(NotFoundError):
            await service.get_resume(created.id, user2.id)

    async def test_update_resume(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        created = await service.create_resume(user.id, title="Original")
        updated = await service.update_resume(created.id, user.id, {"title": "Updated", "description": "Changed"})
        assert updated.title == "Updated"
        assert updated.description == "Changed"

    async def test_update_resume_wrong_user(self, db_session):
        user1 = await _create_user(db_session, "upd1@test.com")
        user2 = await _create_user(db_session, "upd2@test.com")
        service = ResumeService(db_session)
        created = await service.create_resume(user1.id, title="Mine")
        with pytest.raises(NotFoundError):
            await service.update_resume(created.id, user2.id, {"title": "Hacked"})

    async def test_delete_resume(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        created = await service.create_resume(user.id, title="To Delete")
        await service.delete_resume(created.id, user.id)
        with pytest.raises(NotFoundError):
            await service.get_resume(created.id, user.id)

    async def test_delete_resume_wrong_user(self, db_session):
        user1 = await _create_user(db_session, "del1@test.com")
        user2 = await _create_user(db_session, "del2@test.com")
        service = ResumeService(db_session)
        created = await service.create_resume(user1.id, title="Mine")
        with pytest.raises(NotFoundError):
            await service.delete_resume(created.id, user2.id)

    async def test_archive_and_restore(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        created = await service.create_resume(user.id, title="Archivable")
        archived = await service.archive_resume(created.id, user.id)
        assert archived.status == "archived"
        assert archived.archived is True
        restored = await service.restore_resume(created.id, user.id)
        assert restored.status == "active"
        assert restored.archived is False

    async def test_set_default_resume(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        r1 = await service.create_resume(user.id, title="First")
        r2 = await service.create_resume(user.id, title="Second")
        assert r1.is_default is True
        assert r2.is_default is False
        await service.set_default_resume(r2.id, user.id)
        default = await service.resume_repo.get_default(user.id)
        assert default.id == r2.id

    async def test_create_version(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        sections = [{"section_type": "summary", "content": {"text": "Original"}}]
        created = await service.create_resume(user.id, title="V1", sections=sections)
        v2 = await service.create_version(created.id, user.id, change_summary="Added experience")
        assert v2.version == 2
        assert v2.previous_version_id == created.id
        assert v2.change_summary == "Added experience"
        assert len(v2.sections) == 1

    async def test_add_section(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        resume = await service.create_resume(user.id, title="Sections Test")
        section = await service.add_section(
            resume.id,
            user.id,
            {"section_type": "summary", "title": "Professional Summary"},
        )
        assert section.id is not None
        assert section.section_type == "summary"
        assert section.title == "Professional Summary"

    async def test_update_section(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        resume = await service.create_resume(user.id, title="Section Update")
        section = await service.add_section(resume.id, user.id, {"section_type": "summary", "title": "Old"})
        updated = await service.update_section(section.id, user.id, {"title": "New", "sort_order": 5})
        assert updated.title == "New"
        assert updated.sort_order == 5

    async def test_delete_section(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        resume = await service.create_resume(user.id, title="Section Delete")
        section = await service.add_section(resume.id, user.id, {"section_type": "summary"})
        await service.delete_section(section.id, user.id)
        with pytest.raises(NotFoundError):
            await service.update_section(section.id, user.id, {"title": "Nope"})

    async def test_add_section_wrong_user(self, db_session):
        user1 = await _create_user(db_session, "sec1@test.com")
        user2 = await _create_user(db_session, "sec2@test.com")
        service = ResumeService(db_session)
        resume = await service.create_resume(user1.id, title="Mine")
        with pytest.raises(NotFoundError):
            await service.add_section(resume.id, user2.id, {"section_type": "summary"})

    async def test_update_section_wrong_user(self, db_session):
        user1 = await _create_user(db_session, "su1@test.com")
        user2 = await _create_user(db_session, "su2@test.com")
        service = ResumeService(db_session)
        resume = await service.create_resume(user1.id, title="Mine")
        section = await service.add_section(resume.id, user1.id, {"section_type": "summary"})
        with pytest.raises(NotFoundError):
            await service.update_section(section.id, user2.id, {"title": "Hacked"})

    async def test_import_resume(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        import_data = ResumeImportData(
            title="Imported Resume",
            description="From JSON",
            template="modern",
            resume_type="professional",
            sections=[
                ResumeSectionCreate(section_type="summary", title="Summary", content={"text": "Hi"}),
            ],
        )
        resume = await service.import_resume(user.id, import_data)
        assert resume.title == "Imported Resume"
        assert resume.source == "manual"
        assert len(resume.sections) == 1

    async def test_export_resume(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        sections = [{"section_type": "summary", "content": {"text": "Export me"}}]
        created = await service.create_resume(user.id, title="Exportable", sections=sections)
        exported = await service.export_resume(created.id, user.id)
        assert exported.id == created.id
        assert len(exported.sections) == 1

    async def test_get_resume_nonexistent(self, db_session):
        user = await _create_user(db_session)
        service = ResumeService(db_session)
        with pytest.raises(NotFoundError):
            await service.get_resume(uuid.uuid4(), user.id)


# ── API Tests ──


class TestResumeAPI:
    @pytest_asyncio.fixture
    async def api_client(self, db_session: AsyncSession):
        app = FastAPI()

        async def _get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = _get_db_override

        @app.exception_handler(NotFoundError)
        async def not_found_handler(request, exc):
            return JSONResponse(status_code=404, content={"detail": exc.message})

        @app.exception_handler(ValidationError)
        async def validation_handler(request, exc):
            return JSONResponse(status_code=400, content={"detail": exc.message})

        @app.exception_handler(AuthenticationError)
        async def auth_error_handler(request, exc):
            return JSONResponse(status_code=401, content={"detail": exc.message})

        @app.exception_handler(ConflictError)
        async def conflict_handler(request, exc):
            return JSONResponse(status_code=409, content={"detail": exc.message})

        app.include_router(resumes_router, prefix="/resumes")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def _auth_headers(self, db_session, user_id: uuid.UUID) -> dict:
        token = create_access_token(subject=str(user_id))
        return {"Authorization": f"Bearer {token}"}

    async def test_unauthenticated(self, api_client):
        resp = await api_client.get("/resumes/")
        assert resp.status_code in (401, 403)

    async def test_create_resume(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        resp = await api_client.post(
            "/resumes/",
            json={"title": "My Resume", "description": "Test"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["title"] == "My Resume"
        assert data["data"]["status"] == "draft"
        assert data["data"]["is_default"] is True

    async def test_create_resume_with_sections(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        payload = {
            "title": "With Sections",
            "sections": [
                {"section_type": "summary", "title": "Summary", "content": {"text": "Hello"}},
                {"section_type": "education", "title": "Education", "sort_order": 1},
            ],
        }
        resp = await api_client.post("/resumes/", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["data"]["sections"]) == 2

    async def test_list_resumes(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await api_client.post("/resumes/", json={"title": "R1"}, headers=headers)
        await api_client.post("/resumes/", json={"title": "R2"}, headers=headers)
        resp = await api_client.get("/resumes/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2

    async def test_get_resume(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Get Test"}, headers=headers)
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.get(f"/resumes/{resume_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Get Test"

    async def test_get_other_users_resume(self, api_client, db_session):
        user1 = await _create_user(db_session, "u1@test.com")
        user2 = await _create_user(db_session, "u2@test.com")
        headers1 = await self._auth_headers(db_session, user1.id)
        headers2 = await self._auth_headers(db_session, user2.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Mine"}, headers=headers1)
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.get(f"/resumes/{resume_id}", headers=headers2)
        assert resp.status_code == 404

    async def test_update_resume(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Original"}, headers=headers)
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.patch(
            f"/resumes/{resume_id}",
            json={"title": "Updated"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated"

    async def test_delete_resume(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Delete Me"}, headers=headers)
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.delete(f"/resumes/{resume_id}", headers=headers)
        assert resp.status_code == 204

    async def test_archive_and_restore(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Archivable"}, headers=headers)
        resume_id = create_resp.json()["data"]["id"]
        archive_resp = await api_client.post(f"/resumes/{resume_id}/archive", headers=headers)
        assert archive_resp.status_code == 200
        assert archive_resp.json()["data"]["status"] == "archived"
        restore_resp = await api_client.post(f"/resumes/{resume_id}/restore", headers=headers)
        assert restore_resp.status_code == 200
        assert restore_resp.json()["data"]["status"] == "active"

    async def test_set_default(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        await api_client.post("/resumes/", json={"title": "R1"}, headers=headers)
        r2 = await api_client.post("/resumes/", json={"title": "R2"}, headers=headers)
        r2_id = r2.json()["data"]["id"]
        resp = await api_client.put(f"/resumes/{r2_id}/default", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["is_default"] is True

    async def test_create_version(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post("/resumes/", json={"title": "V1"}, headers=headers)
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.post(
            f"/resumes/{resume_id}/versions",
            json={"change_summary": "New version"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["version"] == 2
        assert resp.json()["data"]["change_summary"] == "New version"

    async def test_import_resume(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        payload = {
            "title": "Imported",
            "description": "From JSON import",
            "template": "modern",
            "sections": [{"section_type": "summary", "content": {"text": "Hello"}}],
        }
        resp = await api_client.post("/resumes/import", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["title"] == "Imported"
        assert len(data["data"]["sections"]) == 1

    async def test_export_resume(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post(
            "/resumes/",
            json={"title": "Exportable", "sections": [{"section_type": "summary"}]},
            headers=headers,
        )
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.get(f"/resumes/{resume_id}/export", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["version"] == 1
        assert len(data["data"]["sections"]) == 1

    async def test_add_section_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Sections"}, headers=headers)
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.post(
            f"/resumes/{resume_id}/sections",
            json={"section_type": "experience", "title": "Work"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["section_type"] == "experience"

    async def test_update_section_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Sections"}, headers=headers)
        resume_id = create_resp.json()["data"]["id"]
        add_resp = await api_client.post(
            f"/resumes/{resume_id}/sections",
            json={"section_type": "summary", "title": "Old"},
            headers=headers,
        )
        section_id = add_resp.json()["data"]["id"]
        resp = await api_client.patch(
            f"/resumes/{resume_id}/sections/{section_id}",
            json={"title": "New"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "New"

    async def test_delete_section_api(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Sections"}, headers=headers)
        resume_id = create_resp.json()["data"]["id"]
        add_resp = await api_client.post(
            f"/resumes/{resume_id}/sections",
            json={"section_type": "summary"},
            headers=headers,
        )
        section_id = add_resp.json()["data"]["id"]
        resp = await api_client.delete(
            f"/resumes/{resume_id}/sections/{section_id}",
            headers=headers,
        )
        assert resp.status_code == 204

    async def test_list_sections(self, api_client, db_session):
        user = await _create_user(db_session)
        headers = await self._auth_headers(db_session, user.id)
        create_resp = await api_client.post(
            "/resumes/",
            json={"title": "Sections", "sections": [{"section_type": "summary"}, {"section_type": "education"}]},
            headers=headers,
        )
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.get(f"/resumes/{resume_id}/sections", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    async def test_templates_endpoint(self, api_client):
        resp = await api_client.get("/resumes/templates")
        assert resp.status_code == 200
        templates = resp.json()["data"]
        assert len(templates) > 0

    async def test_other_user_cannot_modify_resume(self, api_client, db_session):
        user1 = await _create_user(db_session, "owner@test.com")
        user2 = await _create_user(db_session, "attacker@test.com")
        headers1 = await self._auth_headers(db_session, user1.id)
        headers2 = await self._auth_headers(db_session, user2.id)
        create_resp = await api_client.post("/resumes/", json={"title": "Mine"}, headers=headers1)
        resume_id = create_resp.json()["data"]["id"]
        resp = await api_client.patch(
            f"/resumes/{resume_id}",
            json={"title": "Hacked"},
            headers=headers2,
        )
        assert resp.status_code == 404
