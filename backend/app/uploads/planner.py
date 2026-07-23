from __future__ import annotations

from typing import Any

import structlog

from app.uploads.interfaces import UploadPlanner
from app.uploads.schemas import (
    DocumentType,
    RetryPolicy,
    UploadFieldInfo,
    UploadPlan,
    UploadSource,
    UploadTask,
    UploadTaskType,
    VerificationPolicy,
)

logger = structlog.get_logger(__name__)


class UploadPlannerEngine(UploadPlanner):
    def __init__(self) -> None:
        self._logger = logger.bind(service="upload_planner")

    def plan(self, execution_plan: Any, application_package: Any | None = None) -> UploadPlan:
        plan = UploadPlan()

        steps = getattr(execution_plan, "steps", [])
        for step in steps:
            task = self._create_task(step, application_package)
            plan.tasks.append(task)
            self._tally(plan, task)

        plan.total_tasks = len(plan.tasks)
        plan.execution_plan_ref = getattr(execution_plan, "plan_id", None)

        return plan

    def _create_task(self, step: Any, application_package: Any | None = None) -> UploadTask:
        step_type = getattr(step, "step_type", None)
        step_type_str = str(step_type.value) if hasattr(step_type, "value") else str(step_type)

        field_ref = getattr(step, "field_ref", "")
        selector = getattr(step, "selector", "")
        reason = getattr(step, "reason", "")
        source_path = getattr(step, "source_path", None)

        if step_type_str == "skip" or step_type_str == "Skip":
            return UploadTask(
                task_type=UploadTaskType.SKIP,
                field_ref=field_ref,
                selector=selector,
                document_type=DocumentType.CUSTOM,
                reason=reason or "Skipped by execution plan",
            )

        if step_type_str == "request_manual" or step_type_str == "RequestManual":
            return UploadTask(
                task_type=UploadTaskType.MANUAL,
                field_ref=field_ref,
                selector=selector,
                document_type=DocumentType.CUSTOM,
                reason=reason or "Manual upload required",
                requires_manual_review=True,
            )

        document_type = self._detect_document_type(step, source_path)

        source = None
        if source_path:
            filename = source_path.split("/")[-1].split("\\")[-1] if source_path else None
            source = UploadSource(
                path=source_path,
                document_type=document_type,
                original_filename=filename,
            )

        return UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref=field_ref,
            selector=selector,
            source=source,
            document_type=document_type,
            field_info=UploadFieldInfo(selector=selector),
            retry_policy=RetryPolicy(),
            verification_policy=VerificationPolicy(),
            reason=reason or f"Upload {document_type.value}",
        )

    def _detect_document_type(self, step: Any, source_path: str | None) -> DocumentType:
        step_str = str(getattr(step, "reason", "")).lower()

        doc_keywords = {
            DocumentType.RESUME: ["resume", "cv", "curriculum vitae", "résumé"],
            DocumentType.COVER_LETTER: ["cover letter", "coverletter", "cover_letter", "motivation"],
            DocumentType.PORTFOLIO: ["portfolio", "work sample"],
            DocumentType.TRANSCRIPT: ["transcript", "grades", "academic record"],
            DocumentType.CERTIFICATE: ["certificate", "certification", "license"],
            DocumentType.WORK_SAMPLE: ["work sample", "writing sample", "code sample"],
            DocumentType.SUPPORTING_DOCUMENT: ["supporting", "additional", "other document"],
        }

        for doc_type, keywords in doc_keywords.items():
            for keyword in keywords:
                if keyword in step_str:
                    return doc_type

        if source_path:
            path_lower = source_path.lower()
            if "resume" in path_lower or "cv" in path_lower:
                return DocumentType.RESUME
            if "cover" in path_lower or "motivation" in path_lower:
                return DocumentType.COVER_LETTER
            if "portfolio" in path_lower:
                return DocumentType.PORTFOLIO

        return DocumentType.RESUME

    def _tally(self, plan: UploadPlan, task: UploadTask) -> None:
        if task.task_type == UploadTaskType.UPLOAD:
            plan.upload_tasks += 1
        elif task.task_type == UploadTaskType.SKIP:
            plan.skip_tasks += 1
        elif task.task_type == UploadTaskType.MANUAL:
            plan.manual_tasks += 1
