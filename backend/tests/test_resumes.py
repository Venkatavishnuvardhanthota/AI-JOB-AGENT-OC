import importlib
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.security import get_password_hash
from app.main import app
from app.repositories.user import UserRepository


@pytest_asyncio.fixture
async def test_user(session):
    repo = UserRepository(session)
    user = await repo.create(
        email="resume_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Resume Test User",
    )
    return user


@pytest_asyncio.fixture
async def auth_client(test_user, session):
    from app.api.deps import get_current_user

    async def override_get_db():
        yield session

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ── Resume Master ──

@pytest.mark.asyncio
async def test_create_resume_master(auth_client):
    response = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Software Engineer Resume", "title": "Senior Software Engineer"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Software Engineer Resume"
    assert data["title"] == "Senior Software Engineer"
    assert "id" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_resume_masters(auth_client):
    await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Resume 1", "title": "Engineer"},
    )
    await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Resume 2", "title": "Manager"},
    )
    response = await auth_client.get("/api/v1/resumes/masters")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_resume_master(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "My Resume", "summary": "A great summary"},
    )
    master_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/resumes/masters/{master_id}")
    assert response.status_code == 200
    assert response.json()["summary"] == "A great summary"


@pytest.mark.asyncio
async def test_update_resume_master(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Original Name"},
    )
    master_id = create_resp.json()["id"]
    response = await auth_client.put(
        f"/api/v1/resumes/masters/{master_id}",
        json={"name": "Updated Name", "title": "Lead Developer"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["title"] == "Lead Developer"


@pytest.mark.asyncio
async def test_delete_resume_master(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "To Delete"},
    )
    master_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/resumes/masters/{master_id}")
    assert response.status_code == 204
    response = await auth_client.get(f"/api/v1/resumes/masters/{master_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_resume_master_not_found(auth_client):
    response = await auth_client.get(f"/api/v1/resumes/masters/{uuid.uuid4()}")
    assert response.status_code == 404


# ── Resume Versions ──

@pytest.mark.asyncio
async def test_create_resume_version(auth_client):
    master_resp = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Versioned Resume"},
    )
    master_id = master_resp.json()["id"]
    response = await auth_client.post(
        f"/api/v1/resumes/masters/{master_id}/versions",
        json={"name": "v1", "snapshot_data": {"skills": [{"name": "Python"}]}},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "v1"
    assert data["version_number"] == 1
    assert data["snapshot_data"]["skills"][0]["name"] == "Python"


@pytest.mark.asyncio
async def test_list_resume_versions(auth_client):
    master_resp = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Multi Version Resume"},
    )
    master_id = master_resp.json()["id"]
    await auth_client.post(
        f"/api/v1/resumes/masters/{master_id}/versions",
        json={"name": "v1"},
    )
    await auth_client.post(
        f"/api/v1/resumes/masters/{master_id}/versions",
        json={"name": "v2"},
    )
    response = await auth_client.get(f"/api/v1/resumes/masters/{master_id}/versions")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_version_snapshot(auth_client):
    master_resp = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Snapshot Resume"},
    )
    master_id = master_resp.json()["id"]
    version_resp = await auth_client.post(
        f"/api/v1/resumes/masters/{master_id}/versions",
        json={"name": "v1", "snapshot_data": {"education": [{"institution": "MIT"}]}},
    )
    version_id = version_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/resumes/versions/{version_id}/snapshot")
    assert response.status_code == 200
    assert response.json()["education"][0]["institution"] == "MIT"


# ── Resume Generation ──

@pytest.mark.asyncio
async def test_generate_resume_pdf(auth_client):
    master_resp = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Generate Test"},
    )
    master_id = master_resp.json()["id"]
    version_resp = await auth_client.post(
        f"/api/v1/resumes/masters/{master_id}/versions",
        json={
            "name": "v1",
            "snapshot_data": {
                "profile": {"full_name": "John Doe", "email": "john@example.com"},
                "experience": [{"company": "Acme", "title": "Developer"}],
                "skills": [{"name": "Python"}],
            },
        },
    )
    version_id = version_resp.json()["id"]
    if not importlib.util.find_spec("reportlab"):
        pytest.skip("reportlab not available")

    response = await auth_client.post(
        "/api/v1/resumes/generate",
        json={"resume_version_id": str(version_id), "format": "pdf"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["format"] == "pdf"
    assert data["file_path"] is not None


@pytest.mark.asyncio
async def test_generate_resume_docx(auth_client):
    master_resp = await auth_client.post(
        "/api/v1/resumes/masters",
        json={"name": "Generate DOCX"},
    )
    master_id = master_resp.json()["id"]
    version_resp = await auth_client.post(
        f"/api/v1/resumes/masters/{master_id}/versions",
        json={
            "name": "v1",
            "snapshot_data": {
                "profile": {"full_name": "Jane Doe"},
                "experience": [{"company": "Corp", "title": "Engineer"}],
            },
        },
    )
    version_id = version_resp.json()["id"]
    if not importlib.util.find_spec("docx"):
        pytest.skip("python-docx not available")

    response = await auth_client.post(
        "/api/v1/resumes/generate",
        json={"resume_version_id": str(version_id), "format": "docx"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["format"] == "docx"


# ── Templates ──

@pytest.mark.asyncio
async def test_list_builtin_templates(auth_client):
    response = await auth_client.get("/api/v1/resumes/templates/builtin")
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) >= 3
    names = [t["name"] for t in templates]
    assert "Modern" in names
    assert "Classic" in names
    assert "Minimal" in names


# ── Parser ──

@pytest.mark.asyncio
async def test_parse_resume_txt(auth_client):
    response = await auth_client.post(
        "/api/v1/resumes/parse",
        files={"file": ("resume.txt", b"John Doe\njohn@example.com\n\nSkills: Python, JavaScript")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "john@example.com" in data.get("email", "")


# ── Cross-user isolation ──

@pytest.mark.asyncio
async def test_cross_user_resume_isolation(auth_client, session):
    repo = UserRepository(session)
    other_user = await repo.create(
        email="other_resume@example.com",
        hashed_password=get_password_hash("pass123"),
    )
    await session.flush()

    from app.models.resume_master import ResumeMaster
    from app.repositories.base import BaseRepository
    other_master = await BaseRepository(ResumeMaster, session).create(
        user_id=other_user.id, name="Other's Resume"
    )
    await session.flush()

    response = await auth_client.get(f"/api/v1/resumes/masters/{other_master.id}")
    assert response.status_code == 404
