from __future__ import annotations

import mimetypes
from pathlib import Path

import structlog

from app.uploads.config import UploadsConfig
from app.uploads.exceptions import UploadValidationError
from app.uploads.normalization import get_normalized_document
from app.uploads.schemas import DocumentType, UploadPlan, UploadTaskType

logger = structlog.get_logger(__name__)


class DocumentValidator:
    def __init__(self, config: UploadsConfig | None = None) -> None:
        self._config = config or UploadsConfig()
        self._logger = logger.bind(service="document_validator")

    def validate_file(self, file_path: str, document_type: DocumentType) -> list[str]:
        issues: list[str] = []

        if not file_path or not file_path.strip():
            issues.append("File path is empty")
            return issues

        path = Path(file_path)

        if not path.exists():
            issues.append(f"File does not exist: {file_path}")
            return issues

        if not path.is_file():
            issues.append(f"Path is not a file: {file_path}")
            return issues

        stat = path.stat()
        size_bytes = stat.st_size

        if size_bytes == 0:
            issues.append("File is empty (0 bytes)")

        if size_bytes < self._config.default_min_file_size_bytes:
            issues.append(f"File is below minimum size of {self._config.default_min_file_size_bytes} bytes")

        max_bytes = self._config.max_file_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            issues.append(f"File exceeds maximum size of {self._config.max_file_size_mb}MB")

        ext = path.suffix.lower()
        if ext not in self._config.allowed_extensions:
            allowed = ", ".join(self._config.allowed_extensions)
            issues.append(f"Extension '{ext}' is not allowed. Allowed: {allowed}")

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type not in self._config.allowed_mime_types:
            issues.append(f"MIME type '{mime_type}' is not allowed")

        doc_info = get_normalized_document(document_type)
        if doc_info.extensions and ext not in doc_info.extensions:
            allowed_exts = ", ".join(doc_info.extensions) if doc_info.extensions else "any"
            issues.append(f"Extension '{ext}' is not allowed for {document_type.value}. Allowed: {allowed_exts}")

        if doc_info.mime_types and mime_type and mime_type not in doc_info.mime_types:
            issues.append(f"MIME type '{mime_type}' is not allowed for {document_type.value}")

        return issues

    def validate_plan(self, plan: UploadPlan) -> list[str]:
        issues: list[str] = []

        if not plan.tasks:
            issues.append("no tasks")
            return issues

        seen_refs: set[str] = set()
        for task in plan.tasks:
            if task.field_ref in seen_refs:
                issues.append(f"Duplicate field reference: {task.field_ref}")
            seen_refs.add(task.field_ref)

            if task.task_type == UploadTaskType.UPLOAD:
                if not task.selector:
                    issues.append(f"Upload task {task.task_id} has no selector")
                if task.source and not task.source.path:
                    issues.append(f"Upload task {task.task_id} has no source path")

        return issues

    def validate_file_upload(self, file_path: str, document_type: DocumentType) -> dict[str, str | bool | list[str]]:
        issues = self.validate_file(file_path, document_type)
        if issues:
            raise UploadValidationError(f"File validation failed: {'; '.join(issues)}")
        return {"valid": True, "file_path": file_path, "document_type": document_type.value}
