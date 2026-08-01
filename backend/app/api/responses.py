from __future__ import annotations

import typing as t

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError

if t.TYPE_CHECKING:
    pass


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: t.Any = None,
) -> JSONResponse:
    body: dict[str, t.Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details is not None:
        body["error"]["details"] = details
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        body["error"]["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=body)


def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=str(exc.message),
        details=exc.details or None,
    )


def success_response(
    data: t.Any = None,
    message: str | None = None,
    meta: dict[str, t.Any] | None = None,
) -> dict[str, t.Any]:
    body: dict[str, t.Any] = {"success": True}
    if data is not None:
        body["data"] = data
    if message is not None:
        body["message"] = message
    if meta is not None:
        body["meta"] = meta
    return body
