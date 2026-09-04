import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError as PydanticValidationError

from app.api.responses import error_response, handle_app_error
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_db
from app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import configure_logging, logger
from app.middleware.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESUME_TEMPLATE_DIR, exist_ok=True)
    os.makedirs(settings.BROWSER_SCREENSHOT_DIR, exist_ok=True)

    _run_startup_self_test(app)

    try:
        from app.ai.dependencies import apply_config
        from app.core.database import get_session_factory

        factory = get_session_factory()
        async with factory() as db:
            await apply_config(db)
    except Exception:
        logger.exception("Failed to load persisted AI configuration at startup")

    yield
    await close_db()
    try:
        from app.browser.dependencies import reset_browser_service

        reset_browser_service()
    except Exception:
        logger.exception("Browser cleanup failed during shutdown")
    logger.info("Application shutdown complete.")


def _run_startup_self_test(app: FastAPI) -> None:
    from app.core.self_test import StartupSelfTestService

    svc = StartupSelfTestService()
    result = svc.run()
    app.state.startup_self_test = result
    checks = result["checks"]
    timing = result["duration_ms"]
    max_name_len = max(len(name) for name in checks)
    summary_lines = []
    for name, check in sorted(checks.items()):
        icon = "\u2713" if check["passed"] else "X"
        summary_lines.append(
            f"  {icon} {name.ljust(max_name_len)}  {str(check.get('detail', '')).ljust(50)} {check['duration_ms']} ms"
        )
    summary = "\n".join(summary_lines)
    logger.info(
        "\n==================================================\n"
        "  AI Job Agent Startup\n"
        "==================================================\n"
        "  Version           %s\n"
        "  Startup Self-Test %s  (Completed in %.0f ms)\n"
        "--------------------------------------------------\n"
        "%s\n"
        "==================================================",
        settings.APP_VERSION,
        result["status"],
        timing,
        summary,
    )


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return handle_app_error(request, exc)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return handle_app_error(request, exc)


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return handle_app_error(request, exc)


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    return handle_app_error(request, exc)


@app.exception_handler(AuthorizationError)
async def authorization_handler(request: Request, exc: AuthorizationError):
    return handle_app_error(request, exc)


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return handle_app_error(request, exc)


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_error_handler(request: Request, exc: PydanticValidationError):
    logger.exception("Response serialization failed")
    errors = exc.errors()
    detail = errors[0].get("msg", "Validation error") if errors else "Validation error"
    return error_response(
        request=request,
        status_code=500,
        code="INTERNAL_ERROR",
        message=f"Response serialization failed: {detail}",
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return error_response(
        request=request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check(request: Request):
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


@app.get("/ready")
async def readiness_check(request: Request):
    from app.core.self_test import StartupSelfTestService

    svc = StartupSelfTestService()
    result = svc.run()
    all_passed = all(c["passed"] for c in result["checks"].values())
    return {
        "ready": all_passed,
        "database": result["checks"].get("Database", {}).get("passed", False),
        "ai_system": result["checks"].get("AI System", {}).get("passed", False),
        "provider_registry": result["checks"].get("AI Providers", {}).get("passed", False),
        "prompt_registry": result["checks"].get("Prompt Registry", {}).get("passed", False),
        "configuration": result["checks"].get("Configuration", {}).get("passed", False),
        "version": settings.APP_VERSION,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


@app.get("/health/self-test")
async def health_self_test(request: Request):
    from app.core.self_test import StartupSelfTestService

    svc = StartupSelfTestService()
    result = svc.run()
    return JSONResponse(content=result)
