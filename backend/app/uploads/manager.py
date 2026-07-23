from __future__ import annotations

from typing import Any

import structlog

from app.uploads.capabilities import UploadCapabilityAnalyzer
from app.uploads.executor import UploadExecutorEngine
from app.uploads.planner import UploadPlannerEngine
from app.uploads.schemas import (
    DocumentType,
    UploadPlan,
    UploadRequest,
    UploadResult,
    UploadSource,
    UploadSummary,
    UploadTask,
    UploadTaskResult,
    UploadTaskType,
)
from app.uploads.validator import DocumentValidator
from app.uploads.verification import UploadVerifierEngine

logger = structlog.get_logger(__name__)


class UploadManager:
    def __init__(
        self,
        planner: UploadPlannerEngine | None = None,
        executor: UploadExecutorEngine | None = None,
        verifier: UploadVerifierEngine | None = None,
        validator: DocumentValidator | None = None,
        capability_analyzer: UploadCapabilityAnalyzer | None = None,
    ) -> None:
        self._planner = planner or UploadPlannerEngine()
        self._executor = executor or UploadExecutorEngine()
        self._verifier = verifier or UploadVerifierEngine()
        self._validator = validator or DocumentValidator()
        self._capability_analyzer = capability_analyzer or UploadCapabilityAnalyzer()
        self._logger = logger.bind(service="upload_manager")

    def create_plan(self, execution_plan: Any, application_package: Any | None = None) -> UploadPlan:
        return self._planner.plan(execution_plan, application_package)

    def execute_plan(self, page: Any, plan: UploadPlan) -> list[UploadResult]:
        return self._executor.execute(page, plan)

    def execute_single(self, page: Any, request: UploadRequest) -> UploadResult:
        source = UploadSource(
            path=request.file_path,
            document_type=request.document_type,
            original_filename=request.original_filename,
        )
        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref=request.field_ref or request.document_type.value,
            selector=request.selector or "",
            document_type=request.document_type,
            source=source,
        )

        return self._executor.execute_task(page, task)

    def analyze_field(self, page: Any, selector: str) -> Any:
        return self._capability_analyzer.analyze(page, selector)

    def validate_document(self, file_path: str, document_type: DocumentType) -> list[str]:
        return self._validator.validate_file(file_path, document_type)

    def verify_upload(self, page: Any, task: UploadTask) -> Any:
        return self._verifier.verify(page, task)

    def summarize(self, results: list[UploadResult]) -> UploadSummary:
        summary = UploadSummary()
        if not results:
            return summary

        summary.plan_id = ""

        for r in results:
            summary.total += 1
            if r.result == UploadTaskResult.SUCCESS:
                summary.success += 1
            elif r.result == UploadTaskResult.SKIPPED:
                summary.skipped += 1
            elif r.result == UploadTaskResult.FAILED:
                summary.failed += 1
            elif r.result == UploadTaskResult.TIMEOUT:
                summary.timed_out += 1
            elif r.result == UploadTaskResult.REJECTED:
                summary.rejected += 1
            elif r.result == UploadTaskResult.VERIFICATION_FAILED:
                summary.verification_failed += 1
            elif r.result == UploadTaskResult.MANUAL_REQUIRED:
                summary.manual_required += 1

            if r.duration_ms is not None:
                if summary.total_duration_ms is None:
                    summary.total_duration_ms = 0.0
                summary.total_duration_ms += r.duration_ms

        return summary
