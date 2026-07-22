from __future__ import annotations

from app.job_matching.exceptions import MatchValidationError


class MatchValidator:
    def validate_profile(self, profile) -> list[str]:
        warnings: list[str] = []
        if not profile:
            warnings.append("No profile data provided")
            return warnings
        if hasattr(profile, "completeness") and profile.completeness and profile.completeness.overall_score < 30:
                warnings.append("Profile completeness is very low")
        if not profile.primary_skills and not profile.secondary_skills:
            warnings.append("Profile has no skills defined")
        if profile.years_of_experience is None:
            warnings.append("Profile has no years of experience information")
        if not profile.education_summary:
            warnings.append("Profile has no education information")
        return warnings

    def validate_job(self, job) -> list[str]:
        warnings: list[str] = []
        if not job:
            warnings.append("No job posting provided")
            return warnings
        if hasattr(job, "title") and not job.title:
            warnings.append("Job posting has no title")
        if hasattr(job, "skills") and not job.skills:
            warnings.append("Job posting has no skills listed")
        if (
            hasattr(job, "salary") and job.salary
            and job.salary.min_amount is not None
            and job.salary.max_amount is not None
            and job.salary.min_amount > job.salary.max_amount
        ):
                    warnings.append("Job salary range is invalid (min > max)")
        return warnings

    def assert_valid_input(self, profile, job) -> None:
        profile_issues = self.validate_profile(profile)
        job_issues = self.validate_job(job)
        issues = profile_issues + job_issues
        if issues:
            raise MatchValidationError(
                message="Invalid input for job matching",
                details={"warnings": issues},
            )
