"""Authentication endpoint tests — verifies every protected endpoint rejects unauthorized requests."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.responses import handle_app_error
from app.api.v1.router import api_router
from app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

PROTECTED_ROUTES = [
    ("GET", "/api/v1/ai/providers"),
    ("GET", "/api/v1/ai/providers/openrouter"),
    ("GET", "/api/v1/ai/health"),
    ("GET", "/api/v1/ai/config"),
    ("PUT", "/api/v1/ai/config", {"default_provider": "openai"}),
    ("GET", "/api/v1/ai/models"),
    ("POST", "/api/v1/ai/generate", {"prompt": "hello"}),
    ("GET", "/api/v1/ai/prompts"),
    ("POST", "/api/v1/ai/resume/generate", {"profile_data": "data", "target_role": "role"}),
    ("POST", "/api/v1/ai/cover-letter/generate", {"job_title": "Eng", "company_name": "Acme", "job_description": "desc", "resume_text": "resume"}),
    ("POST", "/api/v1/ai/interview/questions", {"job_title": "Eng", "company": "Acme"}),
    ("POST", "/api/v1/ai/company/research", {"company": "Google"}),
    ("POST", "/api/v1/ai/email/generate", {"email_type": "follow_up", "recipient": "John", "company": "Acme"}),
    ("POST", "/api/v1/ai/matching/enhance", {"job_title": "Eng", "company": "Acme"}),
    ("GET", "/api/v1/jobs/stats"),
]


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.add_exception_handler(AppError, handle_app_error)
    application.add_exception_handler(NotFoundError, handle_app_error)
    application.add_exception_handler(ValidationError, handle_app_error)
    application.add_exception_handler(AuthenticationError, handle_app_error)
    application.add_exception_handler(AuthorizationError, handle_app_error)
    application.add_exception_handler(ConflictError, handle_app_error)
    application.include_router(api_router, prefix="/api/v1")
    return application


@pytest.fixture
async def client(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _json_args(route):
    return route[2] if len(route) > 2 else None


class TestAuthenticationEndpoints:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path", [(r[0], r[1]) for r in PROTECTED_ROUTES])
    async def test_unauthenticated_returns_401(self, client: AsyncClient, method: str, path: str):
        route_data = next(r for r in PROTECTED_ROUTES if r[0] == method and r[1] == path)
        json_body = _json_args(route_data)
        response = await client.request(method, path, json=json_body)
        assert response.status_code == 401, f"{method} {path} returned {response.status_code} instead of 401"

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        response = await client.get("/api/v1/ai/providers", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401
        data = response.json()
        assert data.get("success") is False

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, client: AsyncClient):
        from app.core.security import create_access_token
        from datetime import timedelta

        token = create_access_token(subject=str(uuid.uuid4()), expires_delta=timedelta(seconds=-1))
        response = await client.get("/api/v1/ai/providers", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        data = response.json()
        assert data.get("success") is False
