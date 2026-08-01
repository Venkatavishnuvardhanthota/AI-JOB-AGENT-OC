"""Tests for AI API endpoints."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.v1.ai import router as ai_router
from app.api.deps import get_current_user
from app.api.responses import handle_app_error
from app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class MockUser:
    id = uuid.uuid4()
    is_active = True
    email = "test@example.com"
    first_name = "Test"
    last_name = "User"


def _register_error_handlers(application: FastAPI) -> None:
    application.add_exception_handler(AppError, handle_app_error)
    application.add_exception_handler(NotFoundError, handle_app_error)
    application.add_exception_handler(ValidationError, handle_app_error)
    application.add_exception_handler(AuthenticationError, handle_app_error)
    application.add_exception_handler(AuthorizationError, handle_app_error)
    application.add_exception_handler(ConflictError, handle_app_error)


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    _register_error_handlers(application)
    application.include_router(ai_router, prefix="/ai")
    application.dependency_overrides[get_current_user] = lambda: MockUser()
    return application


@pytest.fixture
async def client(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAIAPIEndpoints:
    @pytest.mark.asyncio
    async def test_get_config(self, client: AsyncClient):
        response = await client.get("/ai/config")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        cfg = data["data"]
        assert "default_provider" in cfg
        assert "default_model" in cfg
        assert "max_retries" in cfg
        assert "timeout_seconds" in cfg
        assert "enabled_providers" in cfg
        assert "streaming_enabled" in cfg

    @pytest.mark.asyncio
    async def test_update_config(self, client: AsyncClient):
        response = await client.put("/ai/config", json={"default_provider": "openai"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "updates" in data["data"]

    @pytest.mark.asyncio
    async def test_list_providers(self, client: AsyncClient):
        response = await client.get("/ai/providers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_get_provider_nonexistent(self, client: AsyncClient):
        response = await client.get("/ai/providers/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_ai_health(self, client: AsyncClient):
        response = await client.get("/ai/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]
        assert "overall_healthy" in data["data"]
        assert "providers" in data["data"]

    @pytest.mark.asyncio
    async def test_list_models(self, client: AsyncClient):
        response = await client.get("/ai/models")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_list_prompts(self, client: AsyncClient):
        response = await client.get("/ai/prompts")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        names = [p["name"] for p in data["data"]]
        assert "resume-generation" in names
        assert "cover-letter" in names
        assert "interview-questions" in names
        assert "company-research" in names
        assert "job-summary" in names
        assert len(data["data"]) >= 8

    @pytest.mark.asyncio
    async def test_generate_empty_prompt(self, client: AsyncClient):
        response = await client.post("/ai/generate", json={"prompt": ""})
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_generate_invalid_provider(self, client: AsyncClient):
        response = await client.post("/ai/generate", json={
            "prompt": "Hello",
            "provider": "nonexistent",
        })
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_test_provider_nonexistent(self, client: AsyncClient):
        response = await client.post("/ai/providers/nonexistent/test")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["healthy"] is False
        assert data["data"]["error"] is not None


class TestAIPromptsRegistration:
    def test_prompt_registry_has_templates(self):
        from app.ai.dependencies import get_prompt_registry
        registry = get_prompt_registry()
        names = registry.list_names()
        assert len(names) >= 8
        assert "resume-generation" in names
        assert "cover-letter" in names
        assert "resume-improvement" in names
        assert "interview-questions" in names
        assert "company-research" in names
        assert "job-summary" in names
        assert "profile-enhancement" in names
        assert "skill-suggestions" in names
        assert "application-questions" in names
        assert "ats-optimization" in names

    def test_prompt_templates_have_content(self):
        from app.ai.dependencies import get_prompt_registry
        registry = get_prompt_registry()
        for t in registry.list():
            assert t.template, f"Template {t.name} has empty template"
            assert t.name, f"Template missing name"

    def test_prompt_variables_extracted(self):
        from app.ai.dependencies import get_prompt_registry
        registry = get_prompt_registry()
        cl_template = registry.get("cover-letter")
        assert "job_title" in cl_template.variables
        assert "company_name" in cl_template.variables
        assert "job_description" in cl_template.variables
        assert "resume_text" in cl_template.variables

        resume_template = registry.get("resume-generation")
        assert "section_type" in resume_template.variables
        assert "job_title" in resume_template.variables

        company_template = registry.get("company-research")
        assert "company" in company_template.variables

        interview_template = registry.get("interview-questions")
        assert "job_title" in interview_template.variables
        assert "count" in interview_template.variables
