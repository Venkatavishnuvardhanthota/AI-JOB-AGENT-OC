from __future__ import annotations

import re

from app.cover_letter.config import CoverLetterConfig
from app.cover_letter.exceptions import CoverLetterValidationError
from app.cover_letter.schemas import GeneratedCoverLetter

UNSUPPORTED_CLAIMS_PATTERNS: list[str] = [
    r"\bI (invented|created|built|developed) the (first|only|best|most)\b",
    r"\b(revolutionized|pioneered|single-handedly|completely)\b",
    r"\b(top \d+|world.?class|industry.?leading)\b",
    r"\b(guarantee|promise) (to |that )\b",
    r"\bI am the (only|best|top)\b",
]


class CoverLetterValidator:
    def __init__(self, config: CoverLetterConfig) -> None:
        self._config = config

    def validate_inputs(self, profile, job_posting, optimized_resume) -> list[str]:
        warnings: list[str] = []
        if not profile:
            warnings.append("No profile intelligence provided")
        if not job_posting:
            warnings.append("No job posting provided")
        else:
            if not self._get_company_name(job_posting):
                warnings.append("Job posting missing company name")
            if not self._get_job_title(job_posting):
                warnings.append("Job posting missing job title")
        if not optimized_resume:
            warnings.append("No optimized resume provided")
        return warnings

    def assert_valid_inputs(self, profile, job_posting, optimized_resume) -> None:
        warnings = self.validate_inputs(profile, job_posting, optimized_resume)
        if warnings and self._config.strict_validation:
            raise CoverLetterValidationError(
                message="Invalid input for cover letter generation",
                details={"warnings": warnings},
            )

    def validate_output(self, cover_letter: GeneratedCoverLetter) -> list[str]:
        warnings: list[str] = []
        if not cover_letter.full_text:
            warnings.append("Generated cover letter is empty")
            return warnings

        word_count = len(cover_letter.full_text.split())
        if word_count > 500:
            warnings.append("Cover letter exceeds recommended length of 500 words")

        if cover_letter.full_text and self._config.strict_validation:
            unsupported = self._check_unsupported_claims(cover_letter.full_text)
            warnings.extend(unsupported)

        return warnings

    def validate_sections(self, sections: list[dict]) -> list[str]:
        warnings: list[str] = []
        seen_paragraphs: set[str] = set()
        for section in sections:
            content = section.get("content", "")
            if content in seen_paragraphs:
                warnings.append(f"Duplicate paragraph content in section '{section.get('section_type')}'")
            seen_paragraphs.add(content)

            word_count = len(content.split())
            if word_count > self._config.max_paragraph_length / 10:
                warnings.append(f"Paragraph in '{section.get('section_type')}' may be too long")
        return warnings

    @staticmethod
    def _check_unsupported_claims(text: str) -> list[str]:
        warnings: list[str] = []
        for pattern in UNSUPPORTED_CLAIMS_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                warnings.append(f"Potentially unsupported claim detected: '{match}'")
        return warnings

    @staticmethod
    def _get_company_name(job_posting) -> str | None:
        if not job_posting:
            return None
        company = getattr(job_posting, "company", None)
        if company:
            return getattr(company, "name", None)
        return None

    @staticmethod
    def _get_job_title(job_posting) -> str | None:
        if not job_posting:
            return None
        return getattr(job_posting, "title", None)
