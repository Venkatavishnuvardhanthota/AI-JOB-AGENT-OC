"""Tests for persisted AI configuration (AISettings + ProviderConfiguration)."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import dependencies as ai_deps
from app.ai.config import AIConfig
from database.models.ai_settings import AISettings
from database.models.provider_configuration import ProviderConfiguration
from database.repositories.ai_settings import AISettingsRepository


@pytest.fixture
def reset_ai_config_store():
    """Snapshot and restore the global AI config store so tests stay isolated."""
    from app.ai.dependencies import _config_store

    before = dict(_config_store)
    yield
    _config_store.clear()
    _config_store.update(before)


class TestAISettingsRepository:
    @pytest.mark.asyncio
    async def test_upsert_creates_then_updates(self, db_session: AsyncSession):
        repo = AISettingsRepository(db_session)
        assert await repo.get() is None

        row = AISettings(default_provider="openai", default_model="gpt-4o", enabled_providers="openai,ollama")
        await repo.upsert(row)
        await db_session.flush()

        fetched = await repo.get()
        assert fetched is not None
        assert fetched.default_provider == "openai"
        assert fetched.enabled_providers == "openai,ollama"

        fetched.default_provider = "gemini"
        fetched.default_model = "gemini-2.0-flash"
        await repo.upsert(fetched)
        await db_session.flush()

        updated = await repo.get()
        assert updated.default_provider == "gemini"
        assert updated.default_model == "gemini-2.0-flash"


class TestBuildConfigFromDB:
    @pytest.mark.asyncio
    async def test_merge_ai_settings_over_env(self, db_session: AsyncSession, reset_ai_config_store):
        repo = AISettingsRepository(db_session)
        await repo.upsert(
            AISettings(
                default_provider="openai",
                default_model="gpt-4o",
                fallback_provider="anthropic",
                fallback_model="claude-3-5-sonnet-20241022",
                temperature=0.2,
                max_tokens=2048,
                timeout_seconds=30,
                max_retries=1,
                retry_delay_seconds=2,
                streaming_enabled=True,
                enabled_providers="openai,anthropic",
            )
        )
        await db_session.flush()

        config = await ai_deps.build_config_from_db(db_session)
        assert config.default_provider == "openai"
        assert config.default_model == "gpt-4o"
        assert config.fallback_provider == "anthropic"
        assert config.temperature == 0.2
        assert config.timeout_seconds == 30
        assert config.max_retries == 1
        assert config.streaming_enabled is True
        assert config.enabled_providers == ["anthropic", "openai"]

    @pytest.mark.asyncio
    async def test_merge_provider_configuration(self, db_session: AsyncSession, reset_ai_config_store):
        db_session.add(
            ProviderConfiguration(
                provider_name="ollama",
                provider_type="ai",
                api_url="http://host.docker.internal:11434",
                default_model="qwen2.5:7b",
                is_enabled=True,
                config=json.dumps({"temperature": 0.1, "timeout_seconds": 20}),
            )
        )
        await db_session.flush()

        config = await ai_deps.build_config_from_db(db_session)
        params = config.provider_params.get("ollama") or {}
        assert params["base_url"] == "http://host.docker.internal:11434"
        assert params["default_model"] == "qwen2.5:7b"
        assert params["temperature"] == 0.1
        assert params["timeout_seconds"] == 20

    @pytest.mark.asyncio
    async def test_disabled_provider_removed_from_enabled(self, db_session: AsyncSession, reset_ai_config_store):
        db_session.add(
            ProviderConfiguration(
                provider_name="gemini",
                provider_type="ai",
                is_enabled=False,
            )
        )
        await db_session.flush()

        config = await ai_deps.build_config_from_db(db_session)
        assert "gemini" not in config.enabled_providers


class TestApplyConfig:
    @pytest.mark.asyncio
    async def test_apply_config_bumps_revision_and_updates_service_config(
        self, db_session: AsyncSession, reset_ai_config_store
    ):
        from app.ai.dependencies import _config_store

        await ai_deps.apply_config(db_session)
        revision_after_first = _config_store["revision"]
        service_config = ai_deps.get_ai_config()
        assert isinstance(service_config, AIConfig)

        repo = AISettingsRepository(db_session)
        await repo.upsert(AISettings(default_provider="anthropic", default_model="claude-sonnet-4-20250514"))
        await db_session.flush()

        await ai_deps.apply_config(db_session)
        assert _config_store["revision"] > revision_after_first
        assert ai_deps.get_ai_config().default_provider == "anthropic"

    @pytest.mark.asyncio
    async def test_re_registration_after_apply(self, db_session: AsyncSession, reset_ai_config_store):
        from app.ai.dependencies import _get_registry, ensure_providers_registered

        await ai_deps.apply_config(db_session)
        ensure_providers_registered()
        registry = _get_registry()
        assert registry.count() > 0

        repo = AISettingsRepository(db_session)
        await repo.upsert(AISettings(default_provider="ollama", default_model="llama3"))
        await db_session.flush()
        await ai_deps.apply_config(db_session)
        ensure_providers_registered()

        assert ai_deps.get_ai_config().default_provider == "ollama"

    @pytest.mark.asyncio
    async def test_apply_config_fallback_on_db_error(self, reset_ai_config_store):
        class BrokenSession:
            async def get(self):
                raise RuntimeError("db down")

            async def list_by_type(self, provider_type: str):
                raise RuntimeError("db down")

        config = await ai_deps.apply_config(BrokenSession())
        assert isinstance(config, AIConfig)
        assert config.default_provider == ai_deps.get_ai_config().default_provider
