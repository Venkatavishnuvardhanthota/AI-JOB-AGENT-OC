from __future__ import annotations

from datetime import datetime, timezone

from app.profile_intelligence.schemas import ValidationIssue, ValidationReport


class ProfileValidator:
    def validate(self, raw: dict) -> ValidationReport:
        issues: list[ValidationIssue] = []
        warnings: list[str] = []

        self._validate_missing_fields(raw, issues, warnings)
        self._validate_duplicate_skills(raw, issues, warnings)
        self._validate_incomplete_work_history(raw, issues, warnings)
        self._validate_date_conflicts(raw, issues, warnings)
        self._validate_conflicting_info(raw, issues, warnings)
        self._validate_missing_resume(raw, warnings)

        return ValidationReport(issues=issues, warnings=warnings)

    def _validate_missing_fields(
        self,
        raw: dict,
        issues: list[ValidationIssue],
        warnings: list[str],
    ) -> None:
        profile = raw.get("profile")
        if not profile:
            warnings.append("No career profile found")
            return

        if not getattr(profile, "headline", None):
            issues.append(
                ValidationIssue(
                    field="headline",
                    severity="info",
                    message="No professional headline set",
                )
            )
        if not getattr(profile, "professional_summary", None):
            issues.append(
                ValidationIssue(
                    field="professional_summary",
                    severity="info",
                    message="No professional summary written",
                )
            )
        if getattr(profile, "total_years_experience", None) is None and not raw.get("experience"):
            issues.append(
                ValidationIssue(
                    field="total_years_experience",
                    severity="warning",
                    message="Years of experience not specified and no work history found",
                )
            )
        if not raw.get("skills"):
            issues.append(
                ValidationIssue(
                    field="skills",
                    severity="warning",
                    message="No skills listed",
                )
            )
        if not raw.get("education"):
            warnings.append("No education history recorded")

    def _validate_duplicate_skills(
        self,
        raw: dict,
        issues: list[ValidationIssue],
        warnings: list[str],
    ) -> None:
        skills = raw.get("skills", [])
        names: list[str] = []
        for s in skills:
            name = (getattr(s, "name", None) or "").lower().strip()
            if name:
                if name in names:
                    issues.append(
                        ValidationIssue(
                            field="skills",
                            severity="warning",
                            message=f"Duplicate skill: {getattr(s, 'name', '')}",
                        )
                    )
                names.append(name)

    def _validate_incomplete_work_history(
        self,
        raw: dict,
        issues: list[ValidationIssue],
        warnings: list[str],
    ) -> None:
        experiences = raw.get("experience", [])
        for exp in experiences:
            start = getattr(exp, "start_date", None)
            end = getattr(exp, "end_date", None)
            currently = getattr(exp, "currently_working", False)
            if start is None:
                issues.append(
                    ValidationIssue(
                        field="experience",
                        severity="warning",
                        message=(
                            f"Missing start date for {getattr(exp, 'title', 'unknown')}"
                            f" at {getattr(exp, 'company', 'unknown')}"
                        ),
                    )
                )
            if end is None and not currently:
                issues.append(
                    ValidationIssue(
                        field="experience",
                        severity="warning",
                        message=(
                            f"Missing end date for {getattr(exp, 'title', 'unknown')}"
                            f" at {getattr(exp, 'company', 'unknown')}"
                            " (not marked as current)"
                        ),
                    )
                )

    def _validate_date_conflicts(
        self,
        raw: dict,
        issues: list[ValidationIssue],
        warnings: list[str],
    ) -> None:
        now = datetime.now(timezone.utc)
        experiences = raw.get("experience", [])
        for exp in experiences:
            end = getattr(exp, "end_date", None)
            if end and isinstance(end, datetime):
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                if end > now:
                    currently = getattr(exp, "currently_working", False)
                    if not currently:
                        issues.append(
                            ValidationIssue(
                                field="experience",
                                severity="warning",
                                message=(
                                    f"End date in the future for"
                                    f" {getattr(exp, 'title', 'unknown')}"
                                    " without current flag"
                                ),
                            )
                        )

        education = raw.get("education", [])
        for edu in education:
            end = getattr(edu, "end_date", None)
            currently = getattr(edu, "currently_studying", False)
            if end and isinstance(end, datetime):
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                if end > now and not currently:
                    issues.append(
                        ValidationIssue(
                            field="education",
                            severity="info",
                            message=(
                                f"Future end date for"
                                f" {getattr(edu, 'institution', 'unknown')}"
                                " without current study flag"
                            ),
                        )
                    )

    def _validate_conflicting_info(
        self,
        raw: dict,
        issues: list[ValidationIssue],
        warnings: list[str],
    ) -> None:
        profile = raw.get("profile")
        if not profile:
            return
        employment_status = getattr(profile, "employment_status", None)
        if (
            employment_status
            and "unemployed" in str(employment_status).lower()
            and getattr(profile, "current_role", None)
        ):
            warnings.append("Employment status is 'unemployed' but current role is specified")

    def _validate_missing_resume(
        self,
        raw: dict,
        warnings: list[str],
    ) -> None:
        has_resume = raw.get("has_resume", False)
        if not has_resume:
            warnings.append("No resume uploaded")
