from __future__ import annotations

import hashlib
import json

from app.application_intelligence.schemas import ApplicationIntelligence
from app.application_package.config import PackageConfig
from app.application_package.schemas import (
    ApplicationPackage,
    PackageStatus,
    PackageValidation,
)
from app.cover_letter.schemas import GeneratedCoverLetter
from app.job_matching.schemas import MatchResult
from app.jobs.schemas import JobPosting
from app.profile_intelligence.schemas import UserIntelligenceProfile
from app.resume_optimization.schemas import OptimizedResume


class PackageGenerator:
    def __init__(self, config: PackageConfig | None = None) -> None:
        self._config = config or PackageConfig()

    def generate(
        self,
        job: JobPosting | None = None,
        profile: UserIntelligenceProfile | None = None,
        application_intelligence: ApplicationIntelligence | None = None,
        match_result: MatchResult | None = None,
        resume: OptimizedResume | None = None,
        cover_letter: GeneratedCoverLetter | None = None,
    ) -> ApplicationPackage:
        validation = self._validate(
            job, profile, application_intelligence, match_result, resume, cover_letter
        )
        completeness = self._calculate_completeness(validation)
        status = self._determine_status(completeness)

        profile_hash = getattr(profile, "profile_hash", None) if profile else None
        job_hash = self.compute_job_hash(job) if job else None
        resume_hash = getattr(resume, "resume_hash", None) if resume else None
        cover_letter_hash = getattr(cover_letter, "id", None) if cover_letter else None
        match_result_hash = getattr(match_result, "id", None) if match_result else None

        package = ApplicationPackage(
            profile_hash=profile_hash,
            job_hash=job_hash,
            resume_hash=resume_hash,
            cover_letter_hash=cover_letter_hash,
            match_result_hash=match_result_hash,
            job=job,
            profile=profile,
            application_intelligence=application_intelligence,
            match_result=match_result,
            resume=resume,
            cover_letter=cover_letter,
            validation=validation,
            completeness_score=completeness,
            status=status,
        )

        package.warnings = list(validation.warnings)
        return package

    def _validate(
        self,
        job: JobPosting | None,
        profile: UserIntelligenceProfile | None,
        application_intelligence: ApplicationIntelligence | None,
        match_result: MatchResult | None,
        resume: OptimizedResume | None,
        cover_letter: GeneratedCoverLetter | None,
    ) -> PackageValidation:
        validation = PackageValidation()

        validation.has_job_posting = job is not None
        validation.has_profile = profile is not None
        validation.has_application_intelligence = application_intelligence is not None
        validation.has_match_result = match_result is not None
        validation.has_resume = resume is not None
        validation.has_cover_letter = cover_letter is not None

        present = [
            validation.has_job_posting,
            validation.has_profile,
            validation.has_application_intelligence,
            validation.has_match_result,
            validation.has_resume,
            validation.has_cover_letter,
        ]
        validation.all_inputs_present = all(present)

        if not validation.has_job_posting:
            validation.warnings.append("Missing job posting")
        if not validation.has_profile:
            validation.warnings.append("Missing profile intelligence")
        if not validation.has_resume:
            validation.warnings.append("Missing optimized resume")
        if not validation.has_cover_letter:
            validation.warnings.append("Missing cover letter")

        if job and not job.title:
            validation.warnings.append("Job posting is missing a title")
        company = getattr(job, "company", None) if job else None
        if job and (not company or not company.name):
            validation.warnings.append("Job posting is missing company name")

        if job and application_intelligence:
            job_company = getattr(company, "name", None)
            ai_company = getattr(
                getattr(application_intelligence, "company", None), "summary", None
            )
            if job_company and ai_company:
                validation.job_consistency_ok = (
                    job_company.lower() in ai_company.lower()
                    or ai_company.lower() in job_company.lower()
                )
                if not validation.job_consistency_ok:
                    validation.warnings.append("Job company name mismatch")
            else:
                validation.job_consistency_ok = True

        if profile and application_intelligence:
            ph = getattr(profile, "profile_hash", None)
            aph = getattr(application_intelligence, "profile_hash", None)
            if ph and aph:
                validation.profile_consistency_ok = ph == aph
                if not validation.profile_consistency_ok:
                    validation.warnings.append("Profile hash mismatch")
            else:
                validation.profile_consistency_ok = True

        return validation

    @staticmethod
    def _calculate_completeness(validation: PackageValidation) -> int:
        score = 0
        if validation.has_job_posting:
            score += 15
        if validation.has_profile:
            score += 15
        if validation.has_application_intelligence:
            score += 10
        if validation.has_match_result:
            score += 10
        if validation.has_resume:
            score += 25
        if validation.has_cover_letter:
            score += 25
        return score

    @staticmethod
    def _determine_status(completeness: int) -> PackageStatus:
        if completeness >= 90:
            return PackageStatus.COMPLETE
        if completeness >= 50:
            return PackageStatus.PARTIAL
        return PackageStatus.INCOMPLETE

    @staticmethod
    def compute_job_hash(job: JobPosting | None) -> str | None:
        if not job:
            return None
        data = {
            "title": getattr(job, "title", None),
            "company": getattr(getattr(job, "company", None), "name", None),
            "skills": getattr(job, "skills", None),
        }
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
