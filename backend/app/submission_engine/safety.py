from __future__ import annotations

from typing import Any

import structlog

from app.submission_engine.config import SubmissionEngineConfig
from app.submission_engine.exceptions import SubmissionSafetyError
from app.submission_engine.interfaces import SafetyGuard
from app.submission_engine.schemas import ExecutionMode, SafetyCheck

logger = structlog.get_logger(__name__)


class SafetyGuardEngine(SafetyGuard):
    def __init__(self, config: SubmissionEngineConfig | None = None) -> None:
        self._config = config or SubmissionEngineConfig()
        self._checks: list[SafetyCheck] = []
        self._mode: ExecutionMode = ExecutionMode.DRY_RUN
        self._logger = logger.bind(service="safety_guard")

    def set_mode(self, mode: ExecutionMode) -> None:
        self._mode = mode
        self._checks.clear()

    def check(self, execution_mode: Any | None = None) -> list[SafetyCheck]:
        mode = execution_mode or self._mode
        self._checks.clear()

        checks_to_run = [
            ("execution_mode_valid", self._check_execution_mode, mode),
            ("page_available", self._check_page_available, None),
            ("submit_allowed_in_mode", self._check_submit_allowed, mode),
        ]

        for check_name, check_fn, arg in checks_to_run:
            check = SafetyCheck(check_name=check_name)
            try:
                result = check_fn(arg) if arg is not None else check_fn()
                check.passed = result["passed"]
                check.details = result["details"]
            except Exception as e:
                check.passed = False
                check.details = str(e)
            self._checks.append(check)

        return list(self._checks)

    def allow_submit(self) -> bool:
        if self._mode == ExecutionMode.DRY_RUN:
            return False
        return self._mode in (
            ExecutionMode.MANUAL_CONFIRMATION,
            ExecutionMode.AUTOMATIC,
            ExecutionMode.SAFE_RETRY,
        )

    def require_manual_confirmation(self) -> bool:
        return self._mode == ExecutionMode.MANUAL_CONFIRMATION

    def is_dry_run(self) -> bool:
        return self._mode == ExecutionMode.DRY_RUN

    def assert_can_submit(self) -> None:
        if not self.allow_submit():
            raise SubmissionSafetyError(
                f"Cannot submit in mode '{self._mode.value}'. "
                f"Use automatic, safe_retry, or manual_confirmation mode."
            )

    def get_checks(self) -> list[SafetyCheck]:
        return list(self._checks)

    def _check_execution_mode(self, mode: ExecutionMode) -> dict:
        if mode.value in self._config.valid_execution_modes:
            return {"passed": True, "details": f"Execution mode '{mode.value}' is valid"}
        return {"passed": False, "details": f"Execution mode '{mode.value}' is not valid"}

    def _check_page_available(self) -> dict:
        return {"passed": True, "details": "Page check deferred to runtime"}

    def _check_submit_allowed(self, mode: ExecutionMode) -> dict:
        if mode == ExecutionMode.DRY_RUN:
            return {"passed": True, "details": "Dry run mode — submit will be simulated"}
        return {"passed": True, "details": f"Submit is allowed in '{mode.value}' mode"}
