from __future__ import annotations

from app.resume_optimization.config import OptimizationConfig
from app.resume_optimization.exceptions import ResumeOptimizationValidationError


class ResumeValidator:
    def __init__(self, config: OptimizationConfig) -> None:
        self._config = config

    def validate_resume(self, resume) -> list[str]:
        warnings: list[str] = []
        if not resume:
            warnings.append("No resume data provided")
            return warnings

        if not self._has_content(resume):
            warnings.append("Resume has no content sections")

        if self._config.validation_strictness == "strict":
            duplicate_skills = self._find_duplicate_skills(resume)
            if duplicate_skills:
                warnings.append(f"Duplicate skills found: {', '.join(duplicate_skills)}")
        return warnings

    def validate_job(self, job) -> list[str]:
        warnings: list[str] = []
        if not job:
            warnings.append("No job posting provided")
            return warnings
        if hasattr(job, "title") and not job.title:
            warnings.append("Job posting has no title")
        if hasattr(job, "skills") and not job.skills:
            warnings.append("Job posting has no required skills listed")
        return warnings

    def validate_profile(self, profile) -> list[str]:
        warnings: list[str] = []
        if not profile:
            warnings.append("No profile intelligence provided")
        return warnings

    def assert_valid_input(self, resume, job, profile) -> None:
        issues = (
            self.validate_resume(resume)
            + self.validate_job(job)
            + self.validate_profile(profile)
        )
        if issues:
            raise ResumeOptimizationValidationError(
                message="Invalid input for resume optimization",
                details={"warnings": issues},
            )

    @staticmethod
    def _has_content(resume) -> bool:
        if hasattr(resume, "sections") and resume.sections:
            return True
        if hasattr(resume, "content") and resume.content:
            return True
        return bool(hasattr(resume, "description") and resume.description)

    @staticmethod
    def _find_duplicate_skills(resume) -> list[str]:
        seen: set[str] = set()
        duplicates: list[str] = []
        sections = getattr(resume, "sections", []) or []
        for section in sections:
            content = getattr(section, "content", None) or {}
            if isinstance(content, dict):
                skills = content.get("skills", []) or []
                for skill in skills:
                    lower = str(skill).lower().strip()
                    if lower in seen:
                        duplicates.append(str(skill))
                    seen.add(lower)
        return duplicates
