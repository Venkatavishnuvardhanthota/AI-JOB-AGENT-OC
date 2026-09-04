from __future__ import annotations

import json
import time
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.dependencies import apply_config, ensure_providers_registered, get_ai_config, get_ai_service
from app.ai.exceptions import (
    AIError,
    ProviderNotFoundError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.ai.schemas import AIProviderConfigUpdate, AIRequest, AIUpdateConfig
from app.ai.service import AIService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import InternalError, NotFoundError, ProviderError

router = APIRouter()


async def _get_ai_service() -> AIService:
    return get_ai_service()


def _provider_entry(name: str, svc: AIService) -> dict[str, Any]:
    """Cheap catalog entry: no network calls to the provider."""
    from app.ai.factory import KNOWN_AI_PROVIDERS

    try:
        provider = svc._registry.resolve(name)
    except ProviderNotFoundError:
        return {"name": name, "display_name": name, "is_available": False, "error": "Provider not registered"}

    errors = provider.validate_config()
    return {
        "name": provider.name,
        "display_name": provider.display_name,
        "description": provider.description,
        "version": provider.version,
        "is_available": len(errors) == 0,
        "supports_streaming": provider.supports_streaming,
        "configured": len(errors) == 0,
        "is_default": name == svc.config.default_provider,
        "capabilities": provider.capabilities.model_dump(),
        "models": [],
        "error": None,
        "implemented": name in KNOWN_AI_PROVIDERS,
    }


async def _saved_config_dict(db: AsyncSession, provider_name: str) -> dict[str, Any] | None:
    from database.repositories.provider_configuration import ProviderConfigurationRepository

    repo = ProviderConfigurationRepository(db)
    row = await repo.get_by_provider_name(provider_name)
    if row is None:
        return None
    extra: dict[str, Any] = {}
    if row.config:
        try:
            extra = json.loads(row.config)
        except (TypeError, ValueError):
            extra = {}
    return {
        "api_key_set": bool(row.api_key),
        "base_url": row.api_url,
        "default_model": row.default_model,
        "is_enabled": row.is_enabled,
        "temperature": extra.get("temperature"),
        "max_tokens": extra.get("max_tokens"),
        "timeout_seconds": extra.get("timeout_seconds"),
        "max_retries": extra.get("max_retries"),
        "retry_delay_seconds": extra.get("retry_delay_seconds"),
        "streaming_enabled": extra.get("streaming_enabled"),
    }


@router.get("/providers", summary="List all AI providers")
async def list_providers(
    ai_service: AIService = Depends(_get_ai_service),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result: list[dict[str, Any]] = []
    for name in ai_service.list_providers():
        entry = _provider_entry(name, ai_service)
        entry["saved_config"] = await _saved_config_dict(db, name)
        result.append(entry)
    return {"success": True, "data": result}


@router.get("/providers/{provider}", summary="Get provider details")
async def get_provider(
    provider: str,
    ai_service: AIService = Depends(_get_ai_service),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        info = await ai_service.provider_info(provider)
    except ProviderNotFoundError:
        raise NotFoundError(f"Provider '{provider}' not found.") from None
    return {
        "success": True,
        "data": {
            "name": info.name,
            "display_name": info.display_name,
            "description": info.description,
            "version": info.version,
            "is_available": info.is_available,
            "supports_streaming": info.supports_streaming,
            "configured": info.configured,
            "is_default": provider == ai_service.config.default_provider,
            "capabilities": info.capabilities.model_dump() if info.capabilities else None,
            "models": [m.model_dump() for m in info.models] if info.models else [],
            "error": info.error,
            "saved_config": await _saved_config_dict(db, provider),
        },
    }


@router.put("/providers/{provider}/config", summary="Save provider configuration")
async def update_provider_config(
    provider: str,
    body: AIProviderConfigUpdate,
    ai_service: AIService = Depends(_get_ai_service),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.ai.factory import KNOWN_AI_PROVIDERS
    from database.models.provider_configuration import ProviderConfiguration
    from database.repositories.provider_configuration import ProviderConfigurationRepository

    if provider not in KNOWN_AI_PROVIDERS:
        raise NotFoundError(f"Provider '{provider}' not found.")

    repo = ProviderConfigurationRepository(db)
    row = await repo.get_by_provider_name(provider)
    if row is None:
        row = ProviderConfiguration(provider_name=provider, provider_type="ai")
        db.add(row)

    if body.api_key is not None:
        row.api_key = body.api_key or None
    if body.base_url is not None:
        row.api_url = body.base_url or None
    if body.default_model is not None:
        row.default_model = body.default_model or None
    if body.is_enabled is not None:
        row.is_enabled = body.is_enabled

    extra: dict[str, Any] = {}
    if row.config:
        try:
            extra = json.loads(row.config)
        except (TypeError, ValueError):
            extra = {}
    for key in (
        "temperature",
        "max_tokens",
        "timeout_seconds",
        "max_retries",
        "retry_delay_seconds",
        "streaming_enabled",
    ):
        value = getattr(body, key)
        if value is not None:
            extra[key] = value
    row.config = json.dumps(extra) if extra else None

    await db.flush()
    await db.commit()
    await apply_config(db)
    ensure_providers_registered()

    return {
        "success": True,
        "data": {
            "message": f"{provider} configuration saved",
            "saved_config": await _saved_config_dict(db, provider),
        },
    }


@router.delete("/providers/{provider}/config", summary="Delete saved provider configuration")
async def delete_provider_config(
    provider: str,
    ai_service: AIService = Depends(_get_ai_service),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.ai.factory import KNOWN_AI_PROVIDERS
    from database.repositories.provider_configuration import ProviderConfigurationRepository

    if provider not in KNOWN_AI_PROVIDERS:
        raise NotFoundError(f"Provider '{provider}' not found.")

    repo = ProviderConfigurationRepository(db)
    row = await repo.get_by_provider_name(provider)
    if row is not None:
        await db.delete(row)
        await db.commit()
    await apply_config(db)
    ensure_providers_registered()

    return {
        "success": True,
        "data": {"message": f"{provider} configuration cleared", "deleted": row is not None},
    }


@router.post("/providers/{provider}/test", summary="Test provider connection")
async def test_provider(
    provider: str,
    ai_service: AIService = Depends(_get_ai_service),
    current_user=Depends(get_current_user),
):
    try:
        start = time.monotonic()
        health_results = await ai_service.detailed_health(provider_name=provider)
        elapsed = (time.monotonic() - start) * 1000
        if not health_results:
            return {
                "success": True,
                "data": {
                    "provider": provider,
                    "healthy": False,
                    "latency_ms": round(elapsed, 1),
                    "error": "No health data available",
                },
            }
        result = health_results[0]
        return {
            "success": True,
            "data": {
                "provider": result.provider,
                "healthy": result.healthy,
                "connected": result.connected,
                "latency_ms": result.latency_ms,
                "error": result.error,
            },
        }
    except ProviderNotFoundError:
        raise NotFoundError(f"Provider '{provider}' not found.") from None


@router.get("/models", summary="List all available models")
async def list_models(
    provider: str | None = None,
    ai_service: AIService = Depends(_get_ai_service),
    current_user=Depends(get_current_user),
):
    try:
        models = await ai_service.available_models(provider_name=provider)
        return {"success": True, "data": [m.model_dump() for m in models]}
    except Exception as exc:
        raise InternalError("Failed to retrieve models.") from exc


@router.get("/health", summary="AI health check")
async def ai_health(
    ai_service: AIService = Depends(_get_ai_service),
    current_user=Depends(get_current_user),
):
    try:
        results = await ai_service.detailed_health()
        overall = all(r.healthy for r in results) if results else False
        return {
            "success": True,
            "data": {
                "status": "healthy" if overall else "degraded",
                "overall_healthy": overall,
                "providers": [r.model_dump() for r in results],
            },
        }
    except Exception as exc:
        raise InternalError("AI health check failed.") from exc


@router.get("/config", summary="Get AI configuration")
async def get_config(
    ai_config=Depends(get_ai_config),
    current_user=Depends(get_current_user),
):
    return {
        "success": True,
        "data": {
            "default_provider": ai_config.default_provider,
            "default_model": ai_config.default_model,
            "fallback_model": ai_config.fallback_model,
            "fallback_provider": ai_config.fallback_provider,
            "max_retries": ai_config.max_retries,
            "retry_delay_seconds": ai_config.retry_delay_seconds,
            "timeout_seconds": ai_config.timeout_seconds,
            "temperature": ai_config.temperature,
            "max_tokens": ai_config.max_tokens,
            "enabled_providers": ai_config.enabled_providers,
            "streaming_enabled": ai_config.streaming_enabled,
        },
    }


@router.put("/config", summary="Update AI configuration")
async def update_config(
    body: AIUpdateConfig,
    ai_service: AIService = Depends(_get_ai_service),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from database.models.ai_settings import AISettings
    from database.repositories.ai_settings import AISettingsRepository

    updates: list[str] = []
    repo = AISettingsRepository(db)
    base = await repo.get()
    if base is None:
        current = get_ai_config()
        base = AISettings(
            default_provider=current.default_provider,
            default_model=current.default_model,
            fallback_provider=current.fallback_provider,
            fallback_model=current.fallback_model,
            temperature=current.temperature,
            max_tokens=current.max_tokens,
            timeout_seconds=current.timeout_seconds,
            max_retries=current.max_retries,
            retry_delay_seconds=current.retry_delay_seconds,
            streaming_enabled=current.streaming_enabled,
            enabled_providers=",".join(current.enabled_providers),
        )

    if body.default_provider is not None:
        base.default_provider = body.default_provider
        updates.append("default_provider")
    if body.default_model is not None:
        base.default_model = body.default_model
        updates.append("default_model")
    if body.fallback_provider is not None:
        base.fallback_provider = body.fallback_provider or None
        updates.append("fallback_provider")
    if body.fallback_model is not None:
        base.fallback_model = body.fallback_model or None
        updates.append("fallback_model")
    if body.temperature is not None:
        base.temperature = body.temperature
        updates.append("temperature")
    if body.max_tokens is not None:
        base.max_tokens = body.max_tokens
        updates.append("max_tokens")
    if body.timeout_seconds is not None:
        base.timeout_seconds = body.timeout_seconds
        updates.append("timeout_seconds")
    if body.max_retries is not None:
        base.max_retries = body.max_retries
        updates.append("max_retries")
    if body.retry_delay_seconds is not None:
        base.retry_delay_seconds = body.retry_delay_seconds
        updates.append("retry_delay_seconds")
    if body.streaming_enabled is not None:
        base.streaming_enabled = body.streaming_enabled
        updates.append("streaming_enabled")
    if body.enabled_providers is not None:
        base.enabled_providers = ",".join(body.enabled_providers)
        updates.append("enabled_providers")

    await repo.upsert(base)
    await db.commit()
    await apply_config(db)
    ensure_providers_registered()

    return {
        "success": True,
        "data": {
            "message": "AI configuration saved",
            "updates": updates,
            "note": "Configuration persisted and applied to running providers.",
        },
    }


@router.post("/generate", summary="Generate AI content")
async def generate(
    body: AIRequest,
    ai_service: AIService = Depends(_get_ai_service),
    current_user=Depends(get_current_user),
):
    try:
        response = await ai_service.generate(body)
        return {
            "success": True,
            "data": {
                "content": response.content,
                "model": response.model,
                "provider": response.provider,
                "usage": response.usage.model_dump() if response.usage else None,
                "metadata": response.metadata.model_dump() if response.metadata else None,
                "id": str(response.id),
            },
        }
    except ProviderNotFoundError as exc:
        raise NotFoundError(exc.message) from exc
    except ProviderUnavailableError as exc:
        raise ProviderError(exc.message, details={"code": exc.code}) from exc
    except RateLimitedError as exc:
        from app.core.exceptions import RateLimitError

        raise RateLimitError(exc.message) from exc
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code}) from exc


@router.get("/prompts", summary="List registered prompt templates")
async def list_prompts(
    current_user=Depends(get_current_user),
):
    from app.ai.dependencies import get_prompt_registry

    registry = get_prompt_registry()
    templates = registry.list()
    return {
        "success": True,
        "data": [
            {
                "name": t.name,
                "description": t.description,
                "version": t.version,
                "variables": t.variables,
                "has_system_prompt": bool(t.system_prompt),
            }
            for t in templates
        ],
    }
