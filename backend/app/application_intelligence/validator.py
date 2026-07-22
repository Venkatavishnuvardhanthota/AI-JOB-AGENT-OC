from __future__ import annotations

import re

from app.application_intelligence.schemas import ValidationResult


class ApplicationIntelligenceValidator:
    def validate(self, job) -> ValidationResult:
        result = ValidationResult()
        if not job:
            result.has_incomplete_posting = True
            result.warnings.append("Job posting is empty.")
            return result

        description = getattr(job, "description", None)
        result.has_missing_description = not description or not description.strip()

        title = getattr(job, "title", None)
        company = getattr(job, "company", None)
        result.has_incomplete_posting = (
            result.has_missing_description
            or not title
            or not company
        )

        skills = getattr(job, "skills", None) or []
        result.duplicate_requirements = self._find_duplicate_requirements(
            description or "", skills
        )

        result.conflicting_salary = self._check_salary_conflicts(job)
        result.conflicting_location = self._check_location_conflicts(job)
        result.invalid_employment_type = self._check_employment_type(job)

        if result.has_missing_description:
            result.warnings.append("Job posting is missing a description.")

        if result.conflicting_salary:
            result.warnings.append("Salary information contains conflicts.")

        if result.conflicting_location:
            result.warnings.append("Location information contains conflicts.")

        if result.invalid_employment_type:
            result.warnings.append("Employment type appears invalid or contradictory.")

        return result

    def _find_duplicate_requirements(self, description: str, skills: list[str]) -> list[str]:
        seen: set[str] = set()
        duplicates: list[str] = []
        for skill in skills:
            normalized = skill.lower().strip()
            if normalized in seen:
                duplicates.append(skill)
            seen.add(normalized)

        sentences = re.split(r'[.!?\n]', description)
        seen_phrases: set[str] = set()
        for sentence in sentences:
            phrase = sentence.strip().lower()
            if not phrase:
                continue
            if phrase in seen_phrases:
                duplicates.append(sentence.strip()[:80])
            seen_phrases.add(phrase)

        return duplicates[:10]

    def _check_salary_conflicts(self, job) -> bool:
        salary = getattr(job, "salary", None)
        if not salary:
            return False

        min_amt = getattr(salary, "min_amount", None)
        max_amt = getattr(salary, "max_amount", None)

        return bool(min_amt is not None and max_amt is not None and min_amt > max_amt)

    def _check_location_conflicts(self, job) -> bool:
        loc = getattr(job, "location", None)
        if not loc:
            return False

        remote_type = getattr(loc, "remote_type", None)
        display_name = getattr(loc, "display_name", None)

        if remote_type and display_name:
            rt_str = str(remote_type).lower()
            dn_lower = display_name.lower()
            if rt_str == "remote" and dn_lower not in ("remote", "anywhere"):
                return True

        return False

    def _check_employment_type(self, job) -> bool:
        et = getattr(job, "employment_type", None)
        if not et:
            return False

        et_str = str(et).lower()
        valid_types = {
            "full_time", "part_time", "contract", "temporary",
            "internship", "freelance", "other",
        }
        return et_str not in valid_types
