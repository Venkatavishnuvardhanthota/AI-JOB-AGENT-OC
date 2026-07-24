from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UploadsConfig:
    version: str = "1.0.0"
    max_file_size_mb: int = 25
    default_timeout_ms: float = 60000.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    verify_after_upload: bool = True
    verify_timeout_ms: float = 10000.0
    allowed_extensions: tuple[str, ...] = (
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".zip",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".odt",
        ".md",
    )
    allowed_mime_types: tuple[str, ...] = (
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/rtf",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/svg+xml",
        "application/zip",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.oasis.opendocument.text",
        "text/markdown",
    )
    document_type_extensions: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "resume": (".pdf", ".doc", ".docx", ".txt", ".rtf", ".md"),
            "cover_letter": (".pdf", ".doc", ".docx", ".txt", ".rtf", ".md"),
            "portfolio": (".pdf", ".zip", ".html", ".url"),
            "transcript": (".pdf", ".doc", ".docx"),
            "certificate": (".pdf", ".png", ".jpg", ".jpeg"),
            "work_sample": (".pdf", ".zip", ".doc", ".docx"),
            "supporting_document": (".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"),
            "custom": (),
        }
    )
    document_type_mimes: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "resume": (
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "application/rtf",
                "text/markdown",
            ),
            "cover_letter": (
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "application/rtf",
                "text/markdown",
            ),
            "portfolio": ("application/pdf", "application/zip", "text/html", "text/uri-list"),
            "transcript": (
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            "certificate": ("application/pdf", "image/png", "image/jpeg"),
            "work_sample": (
                "application/pdf",
                "application/zip",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            "supporting_document": (
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "image/png",
                "image/jpeg",
            ),
            "custom": (),
        }
    )
    default_min_file_size_bytes: int = 1
