from __future__ import annotations

import time
from typing import Any

import structlog

from app.submission_engine.exceptions import SubmissionExecutionError
from app.submission_engine.schemas import StepExecution, SubmissionStepResult, SubmissionStepType

logger = structlog.get_logger(__name__)


class FieldExecutorEngine:
    def __init__(self) -> None:
        self._logger = logger.bind(service="field_executor")

    def execute_step(self, page: Any, step: Any) -> StepExecution:
        step_type = self._resolve_step_type(step)
        field_ref = getattr(step, "field_ref", "")
        selector = getattr(step, "selector", "")
        value = getattr(step, "value", None)

        execution = StepExecution(
            step_type=step_type,
            field_ref=field_ref,
            selector=selector,
            result=SubmissionStepResult.RUNNING,
            started_at=__import__("datetime").datetime.utcnow(),
        )

        start = time.time()

        try:
            if step_type == SubmissionStepType.SKIP or step_type == SubmissionStepType.REQUEST_MANUAL:
                execution.result = SubmissionStepResult.SKIPPED
            elif step_type == SubmissionStepType.FILL:
                self._do_fill(page, selector, str(value) if value is not None else "")
                execution.result = SubmissionStepResult.SUCCESS
            elif step_type == SubmissionStepType.SELECT:
                self._do_select(page, selector, str(value) if value is not None else "")
                execution.result = SubmissionStepResult.SUCCESS
            elif step_type == SubmissionStepType.CHECK:
                self._do_check(page, selector, bool(value) if value is not None else True)
                execution.result = SubmissionStepResult.SUCCESS
            elif step_type == SubmissionStepType.UPLOAD:
                execution.result = SubmissionStepResult.SKIPPED
            else:
                execution.result = SubmissionStepResult.SKIPPED

        except Exception as e:
            execution.result = SubmissionStepResult.FAILED
            execution.error = str(e)

        execution.duration_ms = round((time.time() - start) * 1000, 2)
        execution.completed_at = __import__("datetime").datetime.utcnow()
        return execution

    def execute_plan(self, page: Any, execution_plan: Any) -> list[StepExecution]:
        steps = getattr(execution_plan, "steps", [])
        executions: list[StepExecution] = []
        for step in steps:
            result = self.execute_step(page, step)
            executions.append(result)
            if result.result == SubmissionStepResult.FAILED:
                self._logger.warning("Step failed", field_ref=result.field_ref, error=result.error)
        return executions

    def _resolve_step_type(self, step: Any) -> SubmissionStepType:
        step_type = getattr(step, "step_type", None)
        if step_type is None:
            return SubmissionStepType.SKIP
        step_type_str = str(step_type.value) if hasattr(step_type, "value") else str(step_type)

        mapping = {
            "fill": SubmissionStepType.FILL,
            "select": SubmissionStepType.SELECT,
            "check": SubmissionStepType.CHECK,
            "upload": SubmissionStepType.UPLOAD,
            "skip": SubmissionStepType.SKIP,
            "request_manual": SubmissionStepType.REQUEST_MANUAL,
        }
        return mapping.get(step_type_str, SubmissionStepType.SKIP)

    def _do_fill(self, page: Any, selector: str, value: str) -> None:
        if not page:
            raise SubmissionExecutionError("Page is not available")
        try:
            element = page.locator(selector)
            if element is None or not element.is_visible():
                raise SubmissionExecutionError(f"Field '{selector}' is not visible")
            element.fill(value)
        except SubmissionExecutionError:
            raise
        except Exception as e:
            raise SubmissionExecutionError(f"Failed to fill '{selector}': {e}") from e

    def _do_select(self, page: Any, selector: str, value: str) -> None:
        if not page:
            raise SubmissionExecutionError("Page is not available")
        try:
            element = page.locator(selector)
            if element is None or not element.is_visible():
                raise SubmissionExecutionError(f"Select '{selector}' is not visible")
            element.select_option(value)
        except SubmissionExecutionError:
            raise
        except Exception as e:
            raise SubmissionExecutionError(f"Failed to select '{selector}': {e}") from e

    def _do_check(self, page: Any, selector: str, checked: bool) -> None:
        if not page:
            raise SubmissionExecutionError("Page is not available")
        try:
            element = page.locator(selector)
            if element is None or not element.is_visible():
                raise SubmissionExecutionError(f"Checkbox '{selector}' is not visible")
            is_checked = element.is_checked()
            if checked and not is_checked:
                element.check()
            elif not checked and is_checked:
                element.uncheck()
        except SubmissionExecutionError:
            raise
        except Exception as e:
            raise SubmissionExecutionError(f"Failed to check '{selector}': {e}") from e
