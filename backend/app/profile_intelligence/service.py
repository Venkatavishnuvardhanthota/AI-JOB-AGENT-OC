from __future__ import annotations

import hashlib
import json
import time
from threading import Lock

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.profile_intelligence.completeness import ProfileCompletenessScorer
from app.profile_intelligence.extractor import ProfileExtractor
from app.profile_intelligence.schemas import (
    UserIntelligenceProfile,
)
from app.profile_intelligence.summarizer import ProfileSummarizer
from app.profile_intelligence.validator import ProfileValidator
from app.repositories import (
    CareerProfileRepository,
    ResumeVersionRepository,
)

logger = structlog.get_logger(__name__)


class ProfileIntelligenceService:
    def __init__(
        self,
        session: AsyncSession,
        cache_ttl_seconds: int = 300,
    ) -> None:
        self._session = session
        self._profile_repo = CareerProfileRepository(session)
        self._resume_repo = ResumeVersionRepository(session)
        self._extractor = ProfileExtractor()
        self._scorer = ProfileCompletenessScorer()
        self._validator = ProfileValidator()
        self._summarizer = ProfileSummarizer()
        self._cache: dict[str, tuple[float, UserIntelligenceProfile]] = {}
        self._cache_ttl = cache_ttl_seconds
        self._cache_lock = Lock()

    async def get_profile_intelligence(
        self,
        user_id,
        skip_cache: bool = False,
    ) -> UserIntelligenceProfile:
        if not skip_cache:
            cached = self._get_cached(str(user_id))
            if cached is not None:
                return cached

        raw = await self._extract_raw_profile(user_id)
        profile = self._build_intelligence_profile(user_id, raw)

        self._set_cache(str(user_id), profile)
        return profile

    def invalidate_cache(self, user_id) -> None:
        with self._cache_lock:
            self._cache.pop(str(user_id), None)

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()

    def _get_cached(self, key: str) -> UserIntelligenceProfile | None:
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            timestamp, profile = entry
            if time.monotonic() - timestamp >= self._cache_ttl:
                del self._cache[key]
                return None
            return profile

    def _set_cache(self, key: str, profile: UserIntelligenceProfile) -> None:
        with self._cache_lock:
            self._cache[key] = (time.monotonic(), profile)

    async def _extract_raw_profile(self, user_id) -> dict:
        try:
            profile = await self._profile_repo.get_by_user(
                user_id,
                load_relations=True,
            )
        except Exception as exc:
            logger.error("Failed to load career profile", user_id=user_id, error=str(exc))
            profile = None

        experiences = []
        education = []
        projects = []
        skills = []
        certifications = []
        languages = []
        social_links = []
        preferences = None

        if profile:
            experiences = (
                profile.experience
                if hasattr(profile, "experience") and profile.experience is not None
                else []
            )
            education = (
                profile.education
                if hasattr(profile, "education") and profile.education is not None
                else []
            )
            projects = (
                profile.projects
                if hasattr(profile, "projects") and profile.projects is not None
                else []
            )
            skills = (
                profile.skills
                if hasattr(profile, "skills") and profile.skills is not None
                else []
            )
            certifications = (
                profile.certifications
                if hasattr(profile, "certifications") and profile.certifications is not None
                else []
            )
            languages = (
                profile.languages
                if hasattr(profile, "languages") and profile.languages is not None
                else []
            )
            social_links = (
                profile.social_links
                if hasattr(profile, "social_links") and profile.social_links is not None
                else []
            )
            preferences = (
                profile.preferences
                if hasattr(profile, "preferences") and profile.preferences is not None
                else None
            )

        try:
            resumes = await self._resume_repo.list_by_user(user_id)
            has_resume = len(resumes) > 0
        except Exception as exc:
            logger.error("Failed to load resumes", user_id=user_id, error=str(exc))
            has_resume = False

        return {
            "profile": profile,
            "experience": experiences,
            "education": education,
            "projects": projects,
            "skills": skills,
            "certifications": certifications,
            "languages": languages,
            "social_links": social_links,
            "preferences": preferences,
            "has_resume": has_resume,
        }

    def _build_intelligence_profile(
        self,
        user_id,
        raw: dict,
    ) -> UserIntelligenceProfile:
        profile = raw.get("profile")
        experiences = raw.get("experience", [])
        skills_list = raw.get("skills", [])
        projects_list = raw.get("projects", [])
        certs_list = raw.get("certifications", [])
        languages_list = raw.get("languages", [])
        preferences = raw.get("preferences")

        skill_names = self._extractor.extract_skill_names(skills_list)
        primary, secondary = self._extractor.extract_primary_skills(
            skill_names,
            [getattr(s, "proficiency", None) for s in skills_list],
            [getattr(s, "years_experience", None) for s in skills_list],
        )
        tech_stack = self._extractor.classify_technical_stack(skill_names)

        years_exp = self._extractor.extract_years_of_experience(profile, experiences)

        current_role = getattr(profile, "current_role", None) if profile else None
        career_level = self._extractor.infer_career_level(current_role, years_exp)

        notice_period = getattr(profile, "notice_period", None) if profile else None
        availability = self._extractor.infer_availability(notice_period)

        completeness = self._scorer.compute(raw)
        validation = self._validator.validate(raw)

        intelligence = UserIntelligenceProfile(
            user_id=user_id,
            current_role=current_role,
            career_level=career_level,
            years_of_experience=years_exp,
            primary_skills=primary,
            secondary_skills=secondary,
            technical_stack=tech_stack,
            education_summary=self._extractor.extract_education_summary(raw.get("education", [])),
            certifications=self._extractor.extract_certifications(certs_list),
            projects=self._extractor.extract_projects(projects_list),
            industries=self._extractor.extract_industries(experiences),
            preferred_locations=self._extractor.extract_preferred_locations(preferences),
            remote_preference=self._extractor.extract_remote_preference(preferences),
            employment_preference=self._extractor.extract_employment_preference(preferences),
            salary_expectation=self._extractor.extract_salary_expectation(profile, preferences),
            languages=self._extractor.extract_languages(languages_list),
            strengths=self._extractor.extract_strengths(skills_list, experiences),
            career_goals=self._extractor.extract_career_goals(profile),
            availability=availability,
            completeness=completeness,
            validation=validation,
        )

        intelligence.personal_summary = self._summarizer.generate_personal_summary(
            intelligence,
        )

        intelligence.profile_hash = self._compute_hash(intelligence)
        return intelligence

    def _compute_hash(self, profile: UserIntelligenceProfile) -> str:
        data = profile.model_dump(exclude={"generated_at", "profile_hash", "completeness", "validation"})
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
