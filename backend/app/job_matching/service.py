from __future__ import annotations

import hashlib
import json

from app.job_matching.cache import MatchCache
from app.job_matching.comparator import (
    CareerLevelComparator,
    CertificationsComparator,
    EducationComparator,
    EmploymentTypeComparator,
    ExperienceComparator,
    IndustryComparator,
    LocationComparator,
    ProjectsComparator,
    RemoteComparator,
    SalaryComparator,
    SkillComparator,
)
from app.job_matching.config import MatchingConfig
from app.job_matching.explanations import ExplanationGenerator
from app.job_matching.schemas import MatchResult
from app.job_matching.scoring import ScoringEngine
from app.job_matching.validator import MatchValidator


class JobMatchingService:
    def __init__(
        self,
        config: MatchingConfig | None = None,
    ) -> None:
        self._config = config or MatchingConfig()
        self._skill_comparator = SkillComparator(self._config)
        self._experience_comparator = ExperienceComparator()
        self._education_comparator = EducationComparator()
        self._location_comparator = LocationComparator()
        self._remote_comparator = RemoteComparator()
        self._salary_comparator = SalaryComparator()
        self._employment_type_comparator = EmploymentTypeComparator()
        self._career_level_comparator = CareerLevelComparator()
        self._industry_comparator = IndustryComparator()
        self._certifications_comparator = CertificationsComparator()
        self._projects_comparator = ProjectsComparator()
        self._scoring_engine = ScoringEngine(self._config)
        self._explanation_generator = ExplanationGenerator()
        self._validator = MatchValidator()
        self._cache = MatchCache(self._config)

    def match(
        self,
        profile,
        job,
        skip_cache: bool = False,
    ) -> MatchResult:
        cache_key = self._cache.compute_key(
            getattr(profile, "profile_hash", None) if profile else None,
            str(getattr(job, "id", "")),
        )

        if not skip_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        result = self._compute_match(profile, job)
        self._cache.set(cache_key, result)
        return result

    def invalidate_cache(self, key: str) -> None:
        self._cache.invalidate(key)

    def clear_cache(self) -> None:
        self._cache.clear()

    def _compute_match(self, profile, job) -> MatchResult:
        warnings = self._validator.validate_profile(profile)
        warnings.extend(self._validator.validate_job(job))

        matching_skills, missing_skills, preferred_skills, skills_raw_score = (
            self._skill_comparator.compare(
                profile_skills=self._get_profile_skills(profile),
                job_skills=self._get_job_skills(job),
                profile_primary=getattr(profile, "primary_skills", None),
                profile_secondary=getattr(profile, "secondary_skills", None),
            )
        )

        experience_score = self._experience_comparator.compare(
            profile_years=getattr(profile, "years_of_experience", None) if profile else None,
            job_experience_level=self._get_job_experience_level(job),
            config=self._config,
        )

        education_score = self._education_comparator.compare(
            profile_education=getattr(profile, "education_summary", None) if profile else None,
            job_requirements=None,
        )

        location_score = self._location_comparator.compare(
            profile_locations=getattr(profile, "preferred_locations", None) if profile else None,
            job_city=self._get_job_city(job),
            job_state=self._get_job_state(job),
            job_country=self._get_job_country(job),
            job_display=self._get_job_location_display(job),
        )

        remote_score = self._remote_comparator.compare(
            profile_remote=getattr(profile, "remote_preference", None) if profile else None,
            job_remote_type=self._get_job_remote_type(job),
        )

        salary_score = self._salary_comparator.compare(
            profile_salary_str=getattr(profile, "salary_expectation", None) if profile else None,
            job_salary_min=self._get_job_salary_min(job),
            job_salary_max=self._get_job_salary_max(job),
            config=self._config,
        )

        employment_type_score = self._employment_type_comparator.compare(
            profile_preference=getattr(profile, "employment_preference", None) if profile else None,
            job_type=self._get_job_employment_type(job),
        )

        career_level_score = self._career_level_comparator.compare(
            profile_level=getattr(profile, "career_level", None) if profile else None,
            job_level=self._get_job_experience_level(job),
        )

        industry_score = self._industry_comparator.compare(
            profile_industries=getattr(profile, "industries", None) if profile else None,
            job_industry=self._get_job_industry(job),
        )

        certifications_score = self._certifications_comparator.compare(
            profile_certs=getattr(profile, "certifications", None) if profile else None,
        )

        projects_score = self._projects_comparator.compare(
            profile_projects=getattr(profile, "projects", None) if profile else None,
        )

        overall_score = self._scoring_engine.compute_overall(
            skills_score=skills_raw_score,
            experience_score=experience_score,
            education_score=education_score,
            location_score=location_score,
            remote_score=remote_score,
            salary_score=salary_score,
            employment_type_score=employment_type_score,
            career_level_score=career_level_score,
            industry_score=industry_score,
            certifications_score=certifications_score,
            projects_score=projects_score,
        )

        dimension_scores = self._scoring_engine.compute_dimension_scores(
            skills_score=skills_raw_score,
            experience_score=experience_score,
            education_score=education_score,
            location_score=location_score,
            remote_score=remote_score,
            salary_score=salary_score,
            employment_type_score=employment_type_score,
            career_level_score=career_level_score,
            industry_score=industry_score,
            certifications_score=certifications_score,
            projects_score=projects_score,
        )

        completeness_score = None
        if profile and hasattr(profile, "completeness") and profile.completeness:
            completeness_score = profile.completeness.overall_score

        confidence_score = self._scoring_engine.compute_confidence(
            overall_score, completeness_score
        )
        recommendation = self._scoring_engine.compute_recommendation(overall_score)

        result = MatchResult(
            profile_hash=getattr(profile, "profile_hash", None) if profile else None,
            job_hash=self._compute_job_hash(job),
            overall_match_score=overall_score,
            recommendation=recommendation,
            confidence_score=confidence_score,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            preferred_skills=preferred_skills,
            skills_score=dimension_scores["skills"],
            experience_score=dimension_scores["experience"],
            education_score=dimension_scores["education"],
            location_score=dimension_scores["location"],
            remote_score=dimension_scores["remote"],
            salary_score=dimension_scores["salary"],
            employment_type_score=dimension_scores["employment_type"],
            career_level_score=dimension_scores["career_level"],
            industry_score=dimension_scores["industry"],
            certifications_score=dimension_scores["certifications"],
            projects_score=dimension_scores["projects"],
        )

        result.match_summary = self._explanation_generator.generate_summary(result)
        result.improvement_recommendations = (
            self._explanation_generator.generate_improvement_recommendations(result)
        )

        return result

    @staticmethod
    def _get_profile_skills(profile) -> list[str]:
        if not profile:
            return []
        result = list(getattr(profile, "primary_skills", []) or [])
        result.extend(getattr(profile, "secondary_skills", []) or [])
        if hasattr(profile, "technical_stack") and profile.technical_stack:
            ts = profile.technical_stack
            for cat in ("programming_languages", "frameworks", "databases", "cloud_platforms", "tools"):
                result.extend(getattr(ts, cat, []) or [])
        return result

    @staticmethod
    def _get_job_skills(job) -> list[str]:
        if not job:
            return []
        return list(getattr(job, "skills", []) or [])

    @staticmethod
    def _get_job_experience_level(job) -> str | None:
        if not job:
            return None
        level = getattr(job, "experience_level", None)
        if level:
            return str(level)
        return None

    @staticmethod
    def _get_job_city(job) -> str | None:
        loc = getattr(job, "location", None) if job else None
        if loc:
            return getattr(loc, "city", None)
        return None

    @staticmethod
    def _get_job_state(job) -> str | None:
        loc = getattr(job, "location", None) if job else None
        if loc:
            return getattr(loc, "state", None)
        return None

    @staticmethod
    def _get_job_country(job) -> str | None:
        loc = getattr(job, "location", None) if job else None
        if loc:
            return getattr(loc, "country", None)
        return None

    @staticmethod
    def _get_job_location_display(job) -> str | None:
        loc = getattr(job, "location", None) if job else None
        if loc:
            return getattr(loc, "display_name", None)
        return None

    @staticmethod
    def _get_job_remote_type(job) -> str | None:
        loc = getattr(job, "location", None) if job else None
        if loc:
            rt = getattr(loc, "remote_type", None)
            if rt:
                return str(rt)
        return None

    @staticmethod
    def _get_job_salary_min(job) -> float | None:
        sal = getattr(job, "salary", None) if job else None
        if sal:
            return getattr(sal, "min_amount", None)
        return None

    @staticmethod
    def _get_job_salary_max(job) -> float | None:
        sal = getattr(job, "salary", None) if job else None
        if sal:
            return getattr(sal, "max_amount", None)
        return None

    @staticmethod
    def _get_job_employment_type(job) -> str | None:
        if not job:
            return None
        et = getattr(job, "employment_type", None)
        if et:
            return str(et)
        return None

    @staticmethod
    def _get_job_industry(job) -> str | None:
        company = getattr(job, "company", None) if job else None
        if company:
            return getattr(company, "industry", None)
        return None

    @staticmethod
    def _compute_job_hash(job) -> str | None:
        if not job:
            return None
        data = {}
        data["title"] = getattr(job, "title", None)
        data["skills"] = getattr(job, "skills", None)
        data["employment_type"] = str(getattr(job, "employment_type", ""))
        level = getattr(job, "experience_level", None)
        data["experience_level"] = str(level) if level else None
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
