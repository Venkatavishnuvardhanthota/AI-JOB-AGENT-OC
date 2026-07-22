from __future__ import annotations

import hashlib
import json

from app.application_intelligence.cache import AnalysisCache
from app.application_intelligence.company import CompanyAnalyzer
from app.application_intelligence.config import ApplicationIntelligenceConfig
from app.application_intelligence.culture import CultureAnalyzer
from app.application_intelligence.role import RoleAnalyzer
from app.application_intelligence.schemas import (
    ApplicationIntelligence,
    ApplicationPriority,
    LocationAnalysis,
    SalaryAnalysis,
)
from app.application_intelligence.skills import SkillExtractor
from app.application_intelligence.validator import ApplicationIntelligenceValidator


class ApplicationIntelligenceAnalyzer:
    def __init__(
        self,
        config: ApplicationIntelligenceConfig | None = None,
    ) -> None:
        self._config = config or ApplicationIntelligenceConfig()
        self._company_analyzer = CompanyAnalyzer(self._config)
        self._role_analyzer = RoleAnalyzer(self._config)
        self._skill_extractor = SkillExtractor()
        self._culture_analyzer = CultureAnalyzer()
        self._validator = ApplicationIntelligenceValidator()
        self._cache = AnalysisCache(self._config)

    def analyze(
        self,
        job,
        match_result=None,
        profile_intelligence=None,
        skip_cache: bool = False,
    ) -> ApplicationIntelligence:
        if not skip_cache:
            job_hash = self._compute_job_hash(job)
            profile_hash = (
                getattr(profile_intelligence, "profile_hash", None)
                if profile_intelligence else None
            )
            cached = self._cache.get(self._cache.compute_key(job_hash, profile_hash))
            if cached is not None:
                return cached

        result = self._compute_analysis(job, match_result, profile_intelligence)
        self._cache.set(
            self._cache.compute_key(result.job_hash or "", result.profile_hash),
            result,
        )
        return result

    def _compute_analysis(
        self,
        job,
        match_result,
        profile_intelligence,
    ) -> ApplicationIntelligence:
        job_hash = self._compute_job_hash(job)
        skills = self._skill_extractor.extract(
            job_skills=getattr(job, "skills", None) or [],
            description=getattr(job, "description", None) or "",
        )

        company_intel = self._company_analyzer.analyze(job)
        role_intel = self._role_analyzer.analyze(job, skills)
        validation = self._validator.validate(job)

        salary_analysis = self._analyze_salary(job)
        location_analysis = self._analyze_location(job)

        profile_hash = (
            getattr(profile_intelligence, "profile_hash", None)
            if profile_intelligence else None
        )

        confidence = self._compute_confidence(
            job, company_intel, role_intel, validation
        )
        priority = self._compute_priority(
            confidence, match_result, profile_intelligence
        )

        return ApplicationIntelligence(
            job_hash=job_hash,
            profile_hash=profile_hash,
            company=company_intel,
            role=role_intel,
            salary=salary_analysis,
            location=location_analysis,
            validation=validation,
            application_priority=priority,
            confidence_score=confidence,
            raw_employment_type=str(getattr(job, "employment_type", None) or ""),
            employment_type_analysis=self._analyze_employment_type(job),
        )

    def invalidate_cache(self, key: str) -> None:
        self._cache.invalidate(key)

    def clear_cache(self) -> None:
        self._cache.clear()

    def _analyze_salary(self, job) -> SalaryAnalysis:
        salary = getattr(job, "salary", None)
        if not salary:
            return SalaryAnalysis()

        return SalaryAnalysis(
            min_amount=getattr(salary, "min_amount", None),
            max_amount=getattr(salary, "max_amount", None),
            currency=getattr(salary, "currency", None),
            period=getattr(salary, "period", None),
            is_competitive=None,
            has_conflicts=False,
        )

    def _analyze_location(self, job) -> LocationAnalysis:
        loc = getattr(job, "location", None)
        if not loc:
            return LocationAnalysis()

        remote_type = getattr(loc, "remote_type", None)
        is_remote_possible = None
        if remote_type:
            rt_str = str(remote_type).lower()
            is_remote_possible = rt_str in ("remote", "hybrid")

        return LocationAnalysis(
            city=getattr(loc, "city", None),
            state=getattr(loc, "state", None),
            country=getattr(loc, "country", None),
            remote_type=str(remote_type) if remote_type else None,
            is_remote_possible=is_remote_possible,
        )

    def _analyze_employment_type(self, job) -> str | None:
        et = getattr(job, "employment_type", None)
        if not et:
            return None
        mapping = {
            "full_time": "Full-time position",
            "part_time": "Part-time position",
            "contract": "Contract position",
            "temporary": "Temporary position",
            "internship": "Internship",
            "freelance": "Freelance position",
        }
        return mapping.get(str(et).lower())

    def _compute_confidence(
        self,
        job,
        company_intel,
        role_intel,
        validation,
    ) -> float:
        signals = 0.0
        total_fields = float(self._config.confidence_score_fields)

        if getattr(job, "description", None):
            signals += 1.0

        if getattr(job, "title", None):
            signals += 1.0

        if company_intel.company_type != "unknown":
            signals += 1.0

        if role_intel.seniority != "unknown":
            signals += 1.0

        if role_intel.category != "unknown":
            signals += 1.0

        if company_intel.summary:
            signals += 1.0

        if not validation.has_missing_description:
            signals += 1.0

        score = signals / total_fields if total_fields > 0 else 0.0
        return round(min(score, 1.0), 4)

    def _compute_priority(
        self,
        confidence: float,
        match_result,
        profile_intelligence,
    ) -> ApplicationPriority:
        boosts = 0.0

        if confidence >= self._config.high_priority_threshold:
            boosts += 0.2

        if match_result:
            match_score = getattr(match_result, "overall_match_score", 0) or 0
            if match_score >= 80:
                boosts += 0.3
            elif match_score >= 60:
                boosts += 0.15

        if profile_intelligence:
            completeness = getattr(profile_intelligence, "completeness", None)
            if completeness:
                overall = getattr(completeness, "overall_score", 0) or 0
                if overall >= 80:
                    boosts += 0.1

        combined = min(confidence + boosts, 1.0)
        if combined >= self._config.high_priority_threshold:
            return ApplicationPriority.HIGH
        if combined >= self._config.medium_priority_threshold:
            return ApplicationPriority.MEDIUM
        return ApplicationPriority.LOW

    @staticmethod
    def _compute_job_hash(job) -> str:
        if not job:
            return ""
        data = {
            "title": getattr(job, "title", None),
            "company_name": getattr(getattr(job, "company", None) or None, "name", None),
            "skills": getattr(job, "skills", None),
        }
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
