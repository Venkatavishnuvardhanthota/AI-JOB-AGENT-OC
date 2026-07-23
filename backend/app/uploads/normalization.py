from __future__ import annotations

from app.uploads.schemas import DocumentType, NormalizedDocument

DOCUMENT_TYPE_MAP: dict[str, dict] = {
    "resume": {
        "document_type": DocumentType.RESUME,
        "label": "Resume",
        "extensions": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".md"],
        "mime_types": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "application/rtf",
            "text/markdown",
        ],
        "keywords": ["resume", "cv", "curriculum vitae", "résumé", "cv.docx", "cv.pdf"],
    },
    "cover_letter": {
        "document_type": DocumentType.COVER_LETTER,
        "label": "Cover Letter",
        "extensions": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".md"],
        "mime_types": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "application/rtf",
            "text/markdown",
        ],
        "keywords": ["cover letter", "coverletter", "cover_letter", "letter", "motivation", "cover"],
    },
    "portfolio": {
        "document_type": DocumentType.PORTFOLIO,
        "label": "Portfolio",
        "extensions": [".pdf", ".zip", ".html", ".url"],
        "mime_types": ["application/pdf", "application/zip", "text/html", "text/uri-list"],
        "keywords": ["portfolio", "work sample", "samples"],
    },
    "transcript": {
        "document_type": DocumentType.TRANSCRIPT,
        "label": "Transcript",
        "extensions": [".pdf", ".doc", ".docx"],
        "mime_types": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ],
        "keywords": ["transcript", "grades", "academic record", "marksheet", "mark sheet"],
    },
    "certificate": {
        "document_type": DocumentType.CERTIFICATE,
        "label": "Certificate",
        "extensions": [".pdf", ".png", ".jpg", ".jpeg"],
        "mime_types": ["application/pdf", "image/png", "image/jpeg"],
        "keywords": ["certificate", "certification", "license", "credential", "diploma"],
    },
    "work_sample": {
        "document_type": DocumentType.WORK_SAMPLE,
        "label": "Work Sample",
        "extensions": [".pdf", ".zip", ".doc", ".docx"],
        "mime_types": [
            "application/pdf",
            "application/zip",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ],
        "keywords": ["work sample", "writing sample", "code sample", "project", "sample"],
    },
    "supporting_document": {
        "document_type": DocumentType.SUPPORTING_DOCUMENT,
        "label": "Supporting Document",
        "extensions": [".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"],
        "mime_types": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/png",
            "image/jpeg",
        ],
        "keywords": ["supporting", "additional", "other", "attachment", "document"],
    },
    "custom": {
        "document_type": DocumentType.CUSTOM,
        "label": "Custom Document",
        "extensions": [],
        "mime_types": [],
        "keywords": ["custom", "other", "additional"],
    },
}


def normalize_label(label: str) -> str:
    normalized = label.lower().strip()
    for ch in (":", "!", "?", "*", "(", ")"):
        normalized = normalized.replace(ch, "")
    normalized = " ".join(normalized.split())
    return normalized


def lookup_document_type(label: str) -> DocumentType:
    normalized = normalize_label(label)
    for _doc_type, info in DOCUMENT_TYPE_MAP.items():
        for keyword in info["keywords"]:
            if keyword in normalized:
                return info["document_type"]
    return DocumentType.CUSTOM


def get_normalized_document(document_type: DocumentType) -> NormalizedDocument:
    info = DOCUMENT_TYPE_MAP.get(document_type.value)
    if info is None:
        return NormalizedDocument(
            document_type=DocumentType.CUSTOM,
            label="Custom Document",
        )
    return NormalizedDocument(**info)
