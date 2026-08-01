from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends

from app.ai.dependencies import get_ai_config, get_ai_service
from app.ai.exceptions import (
    AIError,
    ProviderNotFoundError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.ai.schemas import AIRequest, AIUpdateConfig
from app.ai.service import AIService
from app.api.deps import get_current_user
from app.core.exceptions import InternalError, NotFoundError, ProviderError

router = APIRouter()


async def _get_ai_service() -> AIService:
    return get_ai_service()


@router.get("/providers", summary="List all AI providers")
async def list_providers(
    ai_service: AIService = Depends(_get_ai_service),
    current_user=Depends(get_current_user),
):
    providers = ai_service.list_providers()
    result: list[dict[str, Any]] = []
    for name in providers:
        try:
            info = await ai_service.provider_info(name)
            result.append({
                "name": info.name,
                "display_name": info.display_name,
                "description": info.description,
                "version": info.version,
                "is_available": info.is_available,
                "supports_streaming": info.supports_streaming,
                "configured": info.configured,
                "is_default": name == ai_service.config.default_provider,
                "capabilities": info.capabilities.model_dump() if info.capabilities else None,
                "models": [m.model_dump() for m in info.models] if info.models else [],
                "error": info.error,
            })
        except Exception as exc:
            result.append({
                "name": name,
                "display_name": name,
                "is_available": False,
                "error": str(exc),
            })
    return {"success": True, "data": result}


@router.get("/providers/{provider}", summary="Get provider details")
async def get_provider(
    provider: str,
    ai_service: AIService = Depends(_get_ai_service),
    current_user=Depends(get_current_user),
):
    try:
        info = await ai_service.provider_info(provider)
    except ProviderNotFoundError:
        raise NotFoundError(f"Provider '{provider}' not found.")
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
        },
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
            return {"success": True, "data": {"provider": provider, "healthy": False, "latency_ms": round(elapsed, 1), "error": "No health data available"}}
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
        raise NotFoundError(f"Provider '{provider}' not found.")


@router.get("/models", summary="List all available models")
async def list_models(
    provider: str | None = None,
    ai_service: AIService = Depends(_get_ai_service),
    current_user=Depends(get_current_user),
):
    try:
        models = await ai_service.available_models(provider_name=provider)
        return {"success": True, "data": models}
    except Exception:
        raise InternalError("Failed to retrieve models.")


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
    except Exception:
        raise InternalError("AI health check failed.")


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
    current_user=Depends(get_current_user),
):
    updates: list[str] = []
    if body.default_provider is not None:
        updates.append("default_provider")
    if body.default_model is not None:
        updates.append("default_model")
    if body.temperature is not None:
        updates.append("temperature")
    if body.max_tokens is not None:
        updates.append("max_tokens")
    if body.timeout_seconds is not None:
        updates.append("timeout_seconds")
    if body.max_retries is not None:
        updates.append("max_retries")
    if body.retry_delay_seconds is not None:
        updates.append("retry_delay_seconds")
    if body.streaming_enabled is not None:
        updates.append("streaming_enabled")
    if body.enabled_providers is not None:
        updates.append("enabled_providers")

    return {
        "success": True,
        "data": {
            "message": "Configuration update request received",
            "updates": updates,
            "note": "Runtime configuration changes apply to the current process only.",
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
        raise NotFoundError(exc.message)
    except ProviderUnavailableError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})
    except RateLimitedError as exc:
        from app.core.exceptions import RateLimitError

        raise RateLimitError(exc.message)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


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
