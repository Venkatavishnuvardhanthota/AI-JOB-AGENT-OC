from __future__ import annotations

import time
from typing import Any

import structlog

from app.uploads.exceptions import UploadExecutionError, UploadRejectedError, UploadTimeoutError
from app.uploads.interfaces import UploadExecutor
from app.uploads.schemas import (
    UploadAttempt,
    UploadPlan,
    UploadResult,
    UploadTask,
    UploadTaskResult,
    UploadTaskType,
)
from app.uploads.verification import UploadVerifierEngine

logger = structlog.get_logger(__name__)


class UploadExecutorEngine(UploadExecutor):
    def __init__(self, verifier: UploadVerifierEngine | None = None) -> None:
        self._verifier = verifier or UploadVerifierEngine()
        self._logger = logger.bind(service="upload_executor")

    def execute(self, page: Any, plan: UploadPlan) -> list[UploadResult]:
        results: list[UploadResult] = []
        for task in plan.tasks:
            result = self.execute_task(page, task)
            results.append(result)
        return results

    def execute_task(self, page: Any, task: UploadTask) -> UploadResult:
        if task.task_type == UploadTaskType.SKIP:
            return UploadResult(
                task_id=task.task_id,
                field_ref=task.field_ref,
                result=UploadTaskResult.SKIPPED,
            )

        if task.task_type == UploadTaskType.MANUAL:
            return UploadResult(
                task_id=task.task_id,
                field_ref=task.field_ref,
                result=UploadTaskResult.MANUAL_REQUIRED,
            )

        if task.source is None or not task.source.path:
            return UploadResult(
                task_id=task.task_id,
                field_ref=task.field_ref,
                result=UploadTaskResult.FAILED,
                final_error="No source file specified",
            )

        return self._attempt_upload(page, task)

    def _attempt_upload(self, page: Any, task: UploadTask) -> UploadResult:
        result = UploadResult(
            task_id=task.task_id,
            field_ref=task.field_ref,
            result=UploadTaskResult.PENDING,
        )

        file_path = task.source.path
        selector = task.selector
        timeout_ms = task.retry_policy.max_delay_seconds * 1000

        for attempt_num in range(1, task.retry_policy.max_attempts + 1):
            start = time.time()
            attempt = UploadAttempt(attempt_number=attempt_num)

            try:
                self._do_upload(page, selector, file_path, timeout_ms, task)
                duration = (time.time() - start) * 1000
                attempt.result = UploadTaskResult.SUCCESS
                attempt.duration_ms = round(duration, 2)
                result.attempts.append(attempt)
                result.result = UploadTaskResult.SUCCESS
                result.duration_ms = round(duration, 2)

                if task.verification_policy.verify_after_upload:
                    verify_result = self._verifier.verify(page, task)
                    result.verified = verify_result.verified
                    result.verification_details = verify_result.details
                    if not verify_result.verified:
                        result.result = UploadTaskResult.VERIFICATION_FAILED
                        result.final_error = "Upload verification failed"

                return result

            except UploadTimeoutError as e:
                duration = (time.time() - start) * 1000
                attempt.result = UploadTaskResult.TIMEOUT
                attempt.error_message = str(e)
                attempt.duration_ms = round(duration, 2)
                result.attempts.append(attempt)
                result.result = UploadTaskResult.TIMEOUT
                result.final_error = str(e)

                if attempt_num < task.retry_policy.max_attempts:
                    delay = self._compute_delay(attempt_num, task)
                    time.sleep(delay)

            except UploadRejectedError as e:
                duration = (time.time() - start) * 1000
                attempt.result = UploadTaskResult.REJECTED
                attempt.error_message = str(e)
                attempt.duration_ms = round(duration, 2)
                result.attempts.append(attempt)
                result.result = UploadTaskResult.REJECTED
                result.final_error = str(e)
                break

            except Exception as e:
                duration = (time.time() - start) * 1000
                attempt.result = UploadTaskResult.FAILED
                attempt.error_message = str(e)
                attempt.duration_ms = round(duration, 2)
                result.attempts.append(attempt)
                result.result = UploadTaskResult.FAILED
                result.final_error = str(e)

                if attempt_num < task.retry_policy.max_attempts:
                    delay = self._compute_delay(attempt_num, task)
                    time.sleep(delay)

        return result

    def _do_upload(self, page: Any, selector: str, file_path: str, timeout_ms: float, task: UploadTask) -> None:
        if page is None:
            raise UploadExecutionError("Page is not available")

        try:
            element = page.locator(selector)
            if element is None:
                raise UploadExecutionError(f"Upload element '{selector}' not found")

            if not element.is_visible():
                raise UploadExecutionError(f"Upload element '{selector}' is not visible")

            if task.field_info.multiple and task.source and task.source.path:
                element.set_input_files([file_path], timeout=timeout_ms)
            else:
                element.set_input_files(file_path, timeout=timeout_ms)

        except UploadExecutionError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            if "timeout" in error_str:
                raise UploadTimeoutError(f"Upload timed out for '{selector}': {e}") from e
            if "reject" in error_str or "not allowed" in error_str:
                raise UploadRejectedError(f"Upload rejected for '{selector}': {e}") from e
            raise UploadExecutionError(f"Upload failed for '{selector}': {e}") from e

    def _compute_delay(self, attempt_num: int, task: UploadTask) -> float:
        delay = task.retry_policy.delay_seconds * (task.retry_policy.backoff_multiplier ** (attempt_num - 1))
        return min(delay, task.retry_policy.max_delay_seconds)
