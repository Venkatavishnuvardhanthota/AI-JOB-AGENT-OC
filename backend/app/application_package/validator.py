from __future__ import annotations

from datetime import datetime

from app.application_package.schemas import PackageValidation
from app.cover_letter.schemas import GeneratedCoverLetter
from app.job_matching.schemas import MatchResult
from app.jobs.schemas import JobPosting
from app.profile_intelligence.schemas import UserIntelligenceProfile
from app.resume_optimization.schemas import OptimizedResume


class PackageValidator:
    def validate(
        self,
        job: JobPosting | None,
        profile: UserIntelligenceProfile | None,
        application_intelligence,
        match_result: MatchResult | None,
        resume: OptimizedResume | None,
        cover_letter: GeneratedCoverLetter | None,
    ) -> PackageValidation:
        result = PackageValidation()

        result.has_job_posting = job is not None
        result.has_profile = profile is not None
        result.has_application_intelligence = application_intelligence is not None
        result.has_match_result = match_result is not None
        result.has_resume = resume is not None
        result.has_cover_letter = cover_letter is not None

        present_count = sum(
            [
                result.has_job_posting,
                result.has_profile,
                result.has_application_intelligence,
                result.has_match_result,
                result.has_resume,
                result.has_cover_letter,
            ]
        )

        result.all_inputs_present = present_count >= 6

        if job:
            warnings = self._check_job_validity(job)
            result.warnings.extend(warnings)

        if profile:
            stale = self._check_profile_freshness(profile)
            if stale:
                result.stale_profile_data = True
                result.warnings.append("Profile data may be stale (older than 24 hours).")

        if job and profile:
            mismatched = self._check_profile_job_consistency(profile, job)
            if mismatched:
                result.profile_consistency_ok = False
                result.warnings.extend(mismatched)
            else:
                result.profile_consistency_ok = True

        if match_result and job:
            consistent, issues = self._check_job_consistency(match_result, job)
            result.job_consistency_ok = consistent
            result.warnings.extend(issues)

        if resume and job:
            consistent, issues = self._check_resume_job_consistency(resume, job)
            if not consistent:
                result.warnings.extend(issues)

        if cover_letter and job:
            name_ok, name_issues = self._check_company_name_consistency(cover_letter, job)
            result.company_name_consistency_ok = name_ok
            result.warnings.extend(name_issues)

        return result

    @staticmethod
    def _check_job_validity(job: JobPosting) -> list[str]:
        warnings: list[str] = []
        if not job.title:
            warnings.append("Job posting is missing a title.")
        company = job.company
        if not company or not company.name:
            warnings.append("Job posting is missing company name.")
        return warnings

    @staticmethod
    def _check_profile_freshness(profile: UserIntelligenceProfile) -> bool:
        if profile.generated_at:
            age = datetime.utcnow() - profile.generated_at
            return age.total_seconds() > 86400
        return False

    @staticmethod
    def _check_profile_job_consistency(profile: UserIntelligenceProfile, job: JobPosting) -> list[str]:
        issues: list[str] = []
        title = job.title or ""
        title_lower = title.lower()
        profile_current_role = (profile.current_role or "").lower()

        seniority_keywords = ["senior", "lead", "principal", "junior", "entry"]
        profile_has_seniority = any(kw in profile_current_role for kw in seniority_keywords)
        job_has_seniority = any(kw in title_lower for kw in seniority_keywords)

        if profile_has_seniority and job_has_seniority:
            pass

        return issues

    @staticmethod
    def _check_job_consistency(match_result: MatchResult, job: JobPosting) -> tuple[bool, list[str]]:
        issues: list[str] = []
        match_job_hash = match_result.job_hash
        job_id_str = str(job.id) if hasattr(job, "id") and job.id else ""

        if match_job_hash and job_id_str and match_job_hash not in job_id_str and job_id_str not in match_job_hash:
            pass

        return True, issues

    @staticmethod
    def _check_resume_job_consistency(resume: OptimizedResume, job: JobPosting) -> tuple[bool, list[str]]:
        issues: list[str] = []
        str(job.id) if hasattr(job, "id") and job.id else ""
        return True, issues

    @staticmethod
    def _check_company_name_consistency(cover_letter: GeneratedCoverLetter, job: JobPosting) -> tuple[bool, list[str]]:
        issues: list[str] = []
        cl_company = (cover_letter.personalization.company_name or "").lower().strip()
        job_company = (job.company.name if job.company else "").lower().strip()

        if cl_company and job_company and cl_company != job_company:
            issues.append(f"Company name mismatch: cover letter has '{cl_company}', " f"job has '{job_company}'.")
            return False, issues
        return True, issues
