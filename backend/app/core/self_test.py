from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import structlog

from app.core.config import settings
from app.core.provider_state import (
    IMPLEMENTED_AI_PROVIDERS,
    KNOWN_AI_PROVIDERS,
    get_all_provider_statuses,
)

logger = structlog.get_logger(__name__)


@dataclass
class CheckResult:
    name: str
    passed: bool
    duration_ms: float
    detail: str = ""


class StartupSelfTestService:
    def __init__(self) -> None:
        self._results: dict[str, dict[str, Any]] = {}
        self._overall: str = "PASS"

    def _check(self, name: str, fn: Any) -> None:
        start = time.perf_counter()
        try:
            result = fn()
            passed = True
            detail = str(result) if result is not None else ""
        except Exception as e:
            passed = False
            detail = str(e)
        elapsed = (time.perf_counter() - start) * 1000
        self._results[name] = {
            "passed": passed,
            "duration_ms": round(elapsed, 1),
            "detail": detail,
        }
        if not passed:
            self._overall = "FAIL"

    def run(self) -> dict[str, Any]:
        self._results = {}
        self._overall = "PASS"

        self._check("version", self._check_version)
        self._check("configuration", self._check_configuration)
        self._check("environment", self._check_environment)
        self._check("authentication", self._check_authentication)
        self._check("observability", self._check_observability)
        self._check("database", self._check_database)
        self._check("alembic", self._check_alembic)
        self._check("discovery_providers", self._check_discovery_providers)
        self._check("ai_providers", self._check_ai_providers)
        self._check("ats_providers", self._check_ats_providers)
        self._check("submission_providers", self._check_submission_providers)
        self._check("provider_router", self._check_provider_router)
        self._check("application_engine", self._check_application_engine)
        self._check("browser_framework", self._check_browser_framework)

        total_ms = round(sum(r["duration_ms"] for r in self._results.values()), 1)

        return {
            "status": self._overall,
            "version": settings.APP_VERSION,
            "duration_ms": total_ms,
            "checks": dict(self._results),
        }

    def to_dict(self) -> dict[str, Any]:
        return self.run()

    # Individual checks -------------------------------------------------------

    def _check_version(self) -> str:
        v = settings.APP_VERSION
        if not v:
            raise ValueError("APP_VERSION is empty")
        return f"v{v}"

    def _check_configuration(self) -> str:
        missing = []
        if not settings.APP_NAME:
            missing.append("APP_NAME")
        if not settings.APP_SECRET_KEY:
            missing.append("APP_SECRET_KEY")
        if not settings.DATABASE_URL:
            missing.append("DATABASE_URL")
        if missing:
            raise ValueError(f"Missing configuration: {', '.join(missing)}")
        return "Valid"

    def _check_environment(self) -> str:
        required = ["APP_SECRET_KEY"]
        missing = [k for k in required if not getattr(settings, k, None)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return "Valid"

    def _check_authentication(self) -> str:
        if not settings.APP_SECRET_KEY or len(settings.APP_SECRET_KEY) < 16:
            raise ValueError("APP_SECRET_KEY is too short or missing")
        return "Configured"

    def _check_observability(self) -> str:
        import structlog

        _ = structlog.get_logger()
        return "Configured"

    def _check_database(self) -> str:
        url = settings.DATABASE_URL
        if not url:
            raise ValueError("DATABASE_URL is not set")
        parts = url.split("@")
        host_part = parts[-1].split("/")[0] if len(parts) > 1 else "localhost"
        db_name = url.split("/")[-1] if "/" in url else ""
        return f"Host: {host_part}, Database: {db_name}"

    def _check_alembic(self) -> str:
        try:
            from alembic.config import Config
            from alembic.script import ScriptDirectory

            alembic_cfg = Config("alembic.ini")
            script = ScriptDirectory.from_config(alembic_cfg)
            head = script.get_current_head()
            if not head:
                raise ValueError("No migration head found")
            return f"Head: {head}"
        except Exception as e:
            raise ValueError(f"Alembic check failed: {e}")

    def _check_discovery_providers(self) -> str:
        configured = [p.lower().strip() for p in settings.ENABLED_JOB_PROVIDERS]
        registered = configured  # all configured with implementations are considered registered
        statuses = get_all_provider_statuses(job_configured=configured, job_registered=registered)
        ready = [s["name"] for s in statuses if s["state"] == "ready"]
        pending = [s["name"] for s in statuses if s["state"] != "ready"]
        msg = f"Ready: {len(ready)}"
        if pending:
            msg += f", Pending: {pending}"
        return msg

    def _check_ai_providers(self) -> str:
        configured = [p.lower().strip() for p in settings.AI_ENABLED_PROVIDERS_LIST]
        implemented = [p for p in configured if p in IMPLEMENTED_AI_PROVIDERS]
        not_impl = [p for p in configured if p in KNOWN_AI_PROVIDERS and p not in implemented]
        invalid = [p for p in configured if p not in KNOWN_AI_PROVIDERS]
        parts = []
        if implemented:
            parts.append(f"Registered: {', '.join(implemented)}")
        if not_impl:
            parts.append(f"Not Implemented: {', '.join(not_impl)}")
        if invalid:
            parts.append(f"Invalid: {', '.join(invalid)}")

        default = settings.AI_DEFAULT_PROVIDER.lower().strip()
        if default not in implemented:
            parts.append(f"WARNING: Default provider '{default}' is not in registered providers")
        return "; ".join(parts) if parts else "No AI providers configured"

    def _check_ats_providers(self) -> str:
        configured = [p.lower().strip() for p in settings.ENABLED_JOB_PROVIDERS]
        ats_configured = [p for p in configured if p in {
            "greenhouse", "lever", "ashby", "workday", "smartrecruiters", "bamboohr", "recruitee",
        }]
        if not ats_configured:
            return "None"
        return f"Configured: {', '.join(sorted(ats_configured))}"

    def _check_submission_providers(self) -> str:
        configured = [p.lower().strip() for p in settings.ENABLED_JOB_PROVIDERS]
        sub_configured = [p for p in configured if p in {
            "greenhouse", "lever", "ashby", "workday", "smartrecruiters", "bamboohr", "recruitee",
        }]
        if not sub_configured:
            return "None"
        return f"Configured: {', '.join(sorted(sub_configured))}"

    def _check_provider_router(self) -> str:
        if not settings.ENABLED_JOB_PROVIDERS:
            raise ValueError("No job providers configured")
        return f"Providers: {', '.join(settings.ENABLED_JOB_PROVIDERS)}"

    def _check_application_engine(self) -> str:
        limit = settings.APPLICATIONS_DAILY_LIMIT_DEFAULT
        return f"Daily limit: {limit}"

    def _check_browser_framework(self) -> str:
        enabled = settings.BROWSER_AUTOMATION_ENABLED
        headless = settings.BROWSER_HEADLESS
        return f"Enabled: {enabled}, Headless: {headless}"
