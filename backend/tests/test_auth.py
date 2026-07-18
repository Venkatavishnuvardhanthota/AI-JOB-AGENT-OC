import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_returns_refresh_token(client: AsyncClient):
    email = "refresh_token_test@example.com"
    password = "testpassword123"

    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient):
    email = "refresh_test@example.com"
    password = "testpassword123"

    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token-value"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_revoked_after_use(client: AsyncClient):
    email = "revoke_test@example.com"
    password = "testpassword123"

    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    refresh_token = login_resp.json()["refresh_token"]

    await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient):
    email = "logout_test@example.com"
    password = "testpassword123"

    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    refresh_token = login_resp.json()["refresh_token"]

    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 204

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401
