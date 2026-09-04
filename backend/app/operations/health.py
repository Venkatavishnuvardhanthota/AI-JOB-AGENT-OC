from __future__ import annotations

from datetime import datetime
from typing import Any

from app.operations.config import OperationsConfig
from app.operations.interfaces import HealthChecker
from app.operations.schemas import HealthCheckResult, HealthStatus

_sentinel = object()


class OperationsHealthChecker(HealthChecker):
    def __init__(self, config: OperationsConfig) -> None:
        self._config = config

    def check_application(self) -> dict[str, Any]:
        return self._result("application", HealthStatus.HEALTHY, "Application is running")

    def check_database(self) -> dict[str, Any]:
        try:
            from app.core.config import settings

            value = getattr(settings, "DATABASE_URL", _sentinel)
            if value is _sentinel:
                value = getattr(settings, "database_url", _sentinel)
            if value is not _sentinel and value:
                return self._result("database", HealthStatus.HEALTHY, "Database configured")
            return self._result("database", HealthStatus.DEGRADED, "Database URL not configured")
        except Exception as e:
            return self._result("database", HealthStatus.UNHEALTHY, f"Database check failed: {e}")

    def check_ai_provider(self) -> dict[str, Any]:
        try:
            from app.ai.dependencies import get_ai_service

            svc = get_ai_service()
            available = svc.list_providers()
            if available:
                return self._result("ai_provider", HealthStatus.HEALTHY, f"{len(available)} provider(s) available")
            return self._result("ai_provider", HealthStatus.DEGRADED, "No AI providers available")
        except Exception as e:
            return self._result("ai_provider", HealthStatus.UNHEALTHY, f"AI provider check failed: {e}")

    def check_orchestrator(self) -> dict[str, Any]:
        try:
            from app.orchestrator.dependencies import get_orchestrator_config

            cfg = get_orchestrator_config()
            return self._result(
                "orchestrator", HealthStatus.HEALTHY, f"Orchestrator configured, {cfg.allowed_execution_modes}"
            )
        except Exception as e:
            return self._result("orchestrator", HealthStatus.DEGRADED, f"Orchestrator check failed: {e}")

    def check_all(self) -> dict[str, Any]:
        checks = {
            "application": self.check_application(),
            "database": self.check_database(),
            "ai_provider": self.check_ai_provider(),
            "orchestrator": self.check_orchestrator(),
        }
        statuses = [c["status"] for c in checks.values()]
        overall = HealthStatus.HEALTHY
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall = HealthStatus.DEGRADED
        return {
            "overall": overall.value,
            "checks": checks,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def _result(self, component: str, status: HealthStatus, message: str) -> dict[str, Any]:
        return HealthCheckResult(
            component=component,
            status=status,
            message=message,
        ).model_dump()
