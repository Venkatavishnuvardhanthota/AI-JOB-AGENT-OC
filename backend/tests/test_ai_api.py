"""Tests for AI API endpoints."""

import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.api.responses import handle_app_error
from app.api.v1.ai import router as ai_router
from app.core.database import get_db
from app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from database.models.ai_settings import AISettings
from database.models.provider_configuration import ProviderConfiguration


class MockUser:
    id = uuid.uuid4()
    is_active = True
    email = "test@example.com"
    first_name = "Test"
    last_name = "User"


class _FakeScalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = list(rows)

    def first(self) -> Any | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[Any]:
        return self._rows


class _FakeResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = list(rows)

    def scalars(self) -> _FakeScalars:
        return _FakeScalars(self._rows)

    def unique(self) -> "_FakeResult":
        return self

    def scalar_one_or_none(self) -> Any | None:
        return self._rows[0] if self._rows else None


class FakeSession:
    """In-memory stand-in for the AsyncSession used by config endpoints."""

    def __init__(self) -> None:
        self.settings_row: Any = None
        self.provider_rows: list[Any] = []

    async def execute(self, stmt):
        entity = None
        descriptions = getattr(stmt, "column_descriptions", None)
        if descriptions:
            entity = descriptions[0].get("entity")
        if entity is AISettings:
            rows = [self.settings_row] if self.settings_row is not None else []
        elif entity is ProviderConfiguration:
            rows = list(self.provider_rows)
        else:
            rows = []
        return _FakeResult(rows)

    async def get(self):
        return self.settings_row

    async def upsert(self, settings: Any):
        self.settings_row = settings
        return settings

    async def get_by_provider_name(self, provider_name: str):
        return next((r for r in self.provider_rows if r.provider_name == provider_name), None)

    async def list_by_type(self, provider_type: str):
        return [r for r in self.provider_rows if r.provider_type == provider_type]

    def add(self, obj: Any) -> None:
        if isinstance(obj, AISettings):
            self.settings_row = obj
        elif isinstance(obj, ProviderConfiguration):
            self.provider_rows.append(obj)

    async def delete(self, obj: Any) -> None:
        if isinstance(obj, ProviderConfiguration) and obj in self.provider_rows:
            self.provider_rows.remove(obj)

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        pass


@pytest.fixture
def fake_session() -> FakeSession:
    return FakeSession()


def _register_error_handlers(application: FastAPI) -> None:
    application.add_exception_handler(AppError, handle_app_error)
    application.add_exception_handler(NotFoundError, handle_app_error)
    application.add_exception_handler(ValidationError, handle_app_error)
    application.add_exception_handler(AuthenticationError, handle_app_error)
    application.add_exception_handler(AuthorizationError, handle_app_error)
    application.add_exception_handler(ConflictError, handle_app_error)


@pytest.fixture
def app(fake_session: FakeSession) -> FastAPI:
    application = FastAPI()
    _register_error_handlers(application)
    application.include_router(ai_router, prefix="/ai")
    application.dependency_overrides[get_current_user] = lambda: MockUser()
    application.dependency_overrides[get_db] = lambda: fake_session
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
        assert data["data"]["updates"] == ["default_provider"]

    @pytest.mark.asyncio
    async def test_update_config_persists(self, client: AsyncClient, fake_session: FakeSession):
        response = await client.put(
            "/ai/config",
            json={"default_provider": "gemini", "default_model": "gemini-2.0-flash", "temperature": 0.4},
        )
        assert response.status_code == 200
        assert fake_session.settings_row is not None
        assert fake_session.settings_row.default_provider == "gemini"
        assert fake_session.settings_row.default_model == "gemini-2.0-flash"
        assert fake_session.settings_row.temperature == 0.4

    @pytest.mark.asyncio
    async def test_save_provider_config(self, client: AsyncClient, fake_session: FakeSession):
        response = await client.put(
            "/ai/providers/openai/config",
            json={"api_key": "sk-test", "base_url": "https://custom.openai.com", "default_model": "gpt-4o-mini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["saved_config"]["api_key_set"] is True
        assert fake_session.settings_row is None
        assert any(r.provider_name == "openai" for r in fake_session.provider_rows)

    @pytest.mark.asyncio
    async def test_delete_provider_config(self, client: AsyncClient, fake_session: FakeSession):
        await client.put("/ai/providers/openai/config", json={"api_key": "sk-test"})
        response = await client.delete("/ai/providers/openai/config")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["deleted"] is True
        assert not any(r.provider_name == "openai" for r in fake_session.provider_rows)

    @pytest.mark.asyncio
    async def test_save_provider_config_unknown_provider(self, client: AsyncClient):
        response = await client.put("/ai/providers/unknown-provider/config", json={"api_key": "sk-test"})
        assert response.status_code == 404

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
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_list_models_specific_provider(self, client: AsyncClient):
        response = await client.get("/ai/models?provider=openrouter")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        if data["data"]:
            assert isinstance(data["data"][0], dict)
            assert "id" in data["data"][0]
            assert "provider" in data["data"][0]

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
            assert t.name, "Template missing name"

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
