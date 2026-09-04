from __future__ import annotations

import functools
import inspect
import time
from typing import Any, get_type_hints

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ai_request import AIRequest as AIRequestRecord
from database.models.ai_response import AIResponse as AIResponseRecord

logger = structlog.get_logger(__name__)


async def record_ai_call(
    db: AsyncSession,
    user_id: Any,
    *,
    provider: str,
    model: str | None,
    status: str,
    duration_ms: int | None = None,
    prompt: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    content: str | None = None,
    finish_reason: str | None = None,
) -> None:
    """Persist an AI request/response pair for end-to-end traceability."""
    try:
        record = AIRequestRecord(
            user_id=user_id,
            provider=provider,
            model=model,
            prompt=prompt,
            prompt_tokens=prompt_tokens,
            duration_ms=duration_ms,
            status=status,
        )
        db.add(record)
        await db.flush()
        if content is not None:
            db.add(
                AIResponseRecord(
                    request_id=record.id,
                    content=content,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    model=model,
                    finish_reason=finish_reason,
                )
            )
        await db.flush()
    except Exception:
        logger.exception("Failed to record AI call trace")


def ai_trace(handler: Any) -> Any:
    """Decorator: record each AI feature invocation (provider/model/status/latency) to the database.

    The returned wrapper carries a signature whose annotations are fully resolved so that
    FastAPI (which inspects the wrapper) still recognises pydantic request bodies.
    """

    def _resolved_signature(func: Any) -> inspect.Signature:
        try:
            hints = get_type_hints(func, include_extras=True)
        except Exception:
            hints = {}
        params = []
        for param in inspect.signature(func).parameters.values():
            annotation = hints.get(param.name, param.annotation)
            params.append(param.replace(annotation=annotation))
        return inspect.signature(func).replace(parameters=params)

    signature = _resolved_signature(handler)

    @functools.wraps(handler)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        db = kwargs.get("db")
        current_user = kwargs.get("current_user")
        start = time.monotonic()
        try:
            result = await handler(*args, **kwargs)
            elapsed = int((time.monotonic() - start) * 1000)
            if db is not None and current_user is not None:
                data = result.data if hasattr(result, "data") else result
                await record_ai_call(
                    db,
                    current_user.id,
                    provider=data.get("provider") if isinstance(data, dict) else None,
                    model=data.get("model") if isinstance(data, dict) else None,
                    status="success",
                    duration_ms=elapsed,
                )
            return result
        except Exception:
            elapsed = int((time.monotonic() - start) * 1000)
            if db is not None and current_user is not None:
                await record_ai_call(
                    db,
                    current_user.id,
                    provider="unknown",
                    model=None,
                    status="failed",
                    duration_ms=elapsed,
                )
            raise

    wrapper.__signature__ = signature  # type: ignore[attr-defined]
    return wrapper
