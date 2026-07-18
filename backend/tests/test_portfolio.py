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
        email="portfolio_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Portfolio User",
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


@pytest.mark.asyncio
async def test_create_portfolio_item(auth_client):
    response = await auth_client.post(
        "/api/v1/portfolio",
        json={
            "title": "E-commerce Platform",
            "description": "A full-stack e-commerce platform",
            "url": "https://example.com",
            "technologies": "React, FastAPI, PostgreSQL",
            "is_current": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "E-commerce Platform"
    assert data["technologies"] == "React, FastAPI, PostgreSQL"
    assert data["is_current"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_portfolio_items(auth_client):
    await auth_client.post("/api/v1/portfolio", json={"title": "Project A"})
    await auth_client.post("/api/v1/portfolio", json={"title": "Project B"})
    response = await auth_client.get("/api/v1/portfolio")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_portfolio_item(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/portfolio",
        json={"title": "Specific Project", "url": "https://project.dev"},
    )
    item_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/portfolio/{item_id}")
    assert response.status_code == 200
    assert response.json()["url"] == "https://project.dev"


@pytest.mark.asyncio
async def test_update_portfolio_item(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/portfolio",
        json={"title": "Original Title"},
    )
    item_id = create_resp.json()["id"]
    response = await auth_client.put(
        f"/api/v1/portfolio/{item_id}",
        json={"title": "Updated Title", "description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_portfolio_item(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/portfolio",
        json={"title": "To Delete"},
    )
    item_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/portfolio/{item_id}")
    assert response.status_code == 204
    response = await auth_client.get(f"/api/v1/portfolio/{item_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_portfolio_item_not_found(auth_client):
    response = await auth_client.get(f"/api/v1/portfolio/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_portfolio_media_upload(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/portfolio",
        json={"title": "Media Item", "description": "With image"},
    )
    item_id = create_resp.json()["id"]
    response = await auth_client.post(
        f"/api/v1/portfolio/{item_id}/media",
        files={"file": ("image.png", b"fake-png-content", "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["media_url"] is not None
