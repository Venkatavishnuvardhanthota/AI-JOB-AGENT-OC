import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import (
    Achievement,
    CareerProfile,
    Certification,
    Education,
    Experience,
    Language,
    Project,
    Skill,
    SocialLink,
)
from app.repositories import (
    AchievementRepository,
    CareerProfileRepository,
    CertificationRepository,
    EducationRepository,
    ExperienceRepository,
    JobPreferenceRepository,
    LanguageRepository,
    ProjectRepository,
    SkillRepository,
    SocialLinkRepository,
)
from app.services.audit import AuditService


class CareerProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.profile_repo = CareerProfileRepository(session)
        self.education_repo = EducationRepository(session)
        self.experience_repo = ExperienceRepository(session)
        self.project_repo = ProjectRepository(session)
        self.skill_repo = SkillRepository(session)
        self.certification_repo = CertificationRepository(session)
        self.language_repo = LanguageRepository(session)
        self.social_link_repo = SocialLinkRepository(session)
        self.achievement_repo = AchievementRepository(session)
        self.preference_repo = JobPreferenceRepository(session)
        self.audit_service = AuditService(session)

    async def get_profile(self, user_id: uuid.UUID) -> CareerProfile:
        profile = await self.profile_repo.get_by_user(user_id, load_relations=True)
        if not profile:
            profile = CareerProfile(user_id=user_id)
            profile = await self.profile_repo.create(profile)
            profile = await self.profile_repo.get_by_user(user_id, load_relations=True)
            await self.audit_service.log("PROFILE_CREATED", user_id=user_id, outcome="success")
        return profile

    async def update_profile(self, user_id: uuid.UUID, data: dict) -> CareerProfile:
        profile = await self.get_profile(user_id)
        if "salary_preference" in data:
            preference = data["salary_preference"]
            if preference not in ("paid_only", "paid_preferred", "unpaid_acceptable"):
                raise ValidationError(
                    "Invalid salary preference. Choose paid_only, paid_preferred or unpaid_acceptable."
                )
            if preference == "paid_only" and data.get("expected_salary") is None and profile.expected_salary is None:
                raise ValidationError(
                    "Minimum salary is required when salary preference is set to Paid Only."
                )
        for key, value in data.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)
        await self._recalculate_completeness(profile)
        await self.profile_repo.update(profile)
        await self.audit_service.log("PROFILE_UPDATED", user_id=user_id, outcome="success")
        return profile

    async def delete_profile(self, user_id: uuid.UUID) -> None:
        profile = await self.profile_repo.get_by_user(user_id)
        if not profile:
            raise NotFoundError("Profile not found.")
        await self.profile_repo.delete(profile)
        await self.audit_service.log("PROFILE_DELETED", user_id=user_id, outcome="success")

    # ── Education ──

    async def add_education(self, user_id: uuid.UUID, data: dict) -> Education:
        profile = await self.get_profile(user_id)
        data = self._validate_dates(data, current_field="currently_studying", entity="education")
        edu = Education(profile_id=profile.id, **data)
        created = await self.education_repo.create(edu)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("EDUCATION_ADDED", user_id=user_id, entity="education", outcome="success")
        return created

    async def update_education(self, user_id: uuid.UUID, education_id: uuid.UUID, data: dict) -> Education:
        profile = await self.get_profile(user_id)
        edu = await self.education_repo.get_by_id(education_id)
        if not edu or edu.profile_id != profile.id:
            raise NotFoundError("Education not found.")
        data = self._validate_dates(data, current_field="currently_studying", entity="education")
        for key, value in data.items():
            if value is not None:
                setattr(edu, key, value)
        await self.education_repo.update(edu)
        await self.audit_service.log("EDUCATION_UPDATED", user_id=user_id, entity="education", outcome="success")
        return edu

    async def delete_education(self, user_id: uuid.UUID, education_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        edu = await self.education_repo.get_by_id(education_id)
        if not edu or edu.profile_id != profile.id:
            raise NotFoundError("Education not found.")
        await self.education_repo.delete(edu)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("EDUCATION_DELETED", user_id=user_id, entity="education", outcome="success")

    # ── Experience ──

    async def add_experience(self, user_id: uuid.UUID, data: dict) -> Experience:
        profile = await self.get_profile(user_id)
        data = self._validate_dates(data, current_field="currently_working", entity="experience")
        exp = Experience(profile_id=profile.id, **data)
        created = await self.experience_repo.create(exp)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("EXPERIENCE_ADDED", user_id=user_id, entity="experience", outcome="success")
        return created

    async def update_experience(self, user_id: uuid.UUID, experience_id: uuid.UUID, data: dict) -> Experience:
        profile = await self.get_profile(user_id)
        exp = await self.experience_repo.get_by_id(experience_id)
        if not exp or exp.profile_id != profile.id:
            raise NotFoundError("Experience not found.")
        data = self._validate_dates(data, current_field="currently_working", entity="experience")
        for key, value in data.items():
            if value is not None:
                setattr(exp, key, value)
        await self.experience_repo.update(exp)
        await self.audit_service.log("EXPERIENCE_UPDATED", user_id=user_id, entity="experience", outcome="success")
        return exp

    async def delete_experience(self, user_id: uuid.UUID, experience_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        exp = await self.experience_repo.get_by_id(experience_id)
        if not exp or exp.profile_id != profile.id:
            raise NotFoundError("Experience not found.")
        await self.experience_repo.delete(exp)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("EXPERIENCE_DELETED", user_id=user_id, entity="experience", outcome="success")

    # ── Skills ──

    async def add_skill(self, user_id: uuid.UUID, data: dict) -> Skill:
        profile = await self.get_profile(user_id)
        name = (data.get("name") or "").strip()
        if not name:
            raise ValidationError("Skill name is required.")
        if await self.skill_repo.exists(profile.id, name):
            raise ConflictError(f"Duplicate skill. '{name}' is already in your skills list.")
        skill = Skill(profile_id=profile.id, **data)
        created = await self.skill_repo.create(skill)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("SKILL_ADDED", user_id=user_id, entity="skill", outcome="success")
        return created

    async def update_skill(self, user_id: uuid.UUID, skill_id: uuid.UUID, data: dict) -> Skill:
        profile = await self.get_profile(user_id)
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill or skill.profile_id != profile.id:
            raise NotFoundError("Skill not found.")
        if "name" in data:
            name = (data["name"] or "").strip()
            if not name:
                raise ValidationError("Skill name is required.")
            if await self.skill_repo.exists(profile.id, name) and name.lower() != skill.name.lower():
                raise ConflictError(f"Duplicate skill. '{name}' is already in your skills list.")
            data["name"] = name
        for key, value in data.items():
            if value is not None:
                setattr(skill, key, value)
        await self.skill_repo.update(skill)
        await self.audit_service.log("SKILL_UPDATED", user_id=user_id, entity="skill", outcome="success")
        return skill

    async def delete_skill(self, user_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill or skill.profile_id != profile.id:
            raise NotFoundError("Skill not found.")
        await self.skill_repo.delete(skill)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("SKILL_DELETED", user_id=user_id, entity="skill", outcome="success")

    async def replace_skills(self, user_id: uuid.UUID, names: list[str]) -> list[Skill]:
        profile = await self.get_profile(user_id)
        existing = await self.skill_repo.list_by_profile(profile.id)
        for skill in existing:
            await self.skill_repo.delete(skill)
        cleaned: list[Skill] = []
        seen: set[str] = set()
        for raw in names:
            name = (raw or "").strip()
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            skill = Skill(profile_id=profile.id, name=name)
            cleaned.append(await self.skill_repo.create(skill))
        if not cleaned:
            raise ValidationError("Skill name is required.")
        await self._recalculate_completeness(profile)
        await self.audit_service.log("SKILLS_REPLACED", user_id=user_id, entity="skills", outcome="success")
        return cleaned

    # ── Projects ──

    async def add_project(self, user_id: uuid.UUID, data: dict) -> Project:
        profile = await self.get_profile(user_id)
        name = (data.get("name") or "").strip()
        if not name:
            raise ValidationError("Project name is required.")
        if await self.project_repo.exists_by_name(profile.id, name):
            raise ConflictError(f"Duplicate project. '{name}' is already in your projects list.")
        proj = Project(profile_id=profile.id, **data)
        created = await self.project_repo.create(proj)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("PROJECT_ADDED", user_id=user_id, entity="project", outcome="success")
        return created

    async def update_project(self, user_id: uuid.UUID, project_id: uuid.UUID, data: dict) -> Project:
        profile = await self.get_profile(user_id)
        proj = await self.project_repo.get_by_id(project_id)
        if not proj or proj.profile_id != profile.id:
            raise NotFoundError("Project not found.")
        if "name" in data:
            name = (data["name"] or "").strip()
            if not name:
                raise ValidationError("Project name is required.")
            if await self.project_repo.exists_by_name(profile.id, name) and name.lower() != proj.name.lower():
                raise ConflictError(f"Duplicate project. '{name}' is already in your projects list.")
            data["name"] = name
        for key, value in data.items():
            if value is not None:
                setattr(proj, key, value)
        await self.project_repo.update(proj)
        await self.audit_service.log("PROJECT_UPDATED", user_id=user_id, entity="project", outcome="success")
        return proj

    async def delete_project(self, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        proj = await self.project_repo.get_by_id(project_id)
        if not proj or proj.profile_id != profile.id:
            raise NotFoundError("Project not found.")
        await self.project_repo.delete(proj)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("PROJECT_DELETED", user_id=user_id, entity="project", outcome="success")

    # ── Certifications ──

    async def add_certification(self, user_id: uuid.UUID, data: dict) -> Certification:
        profile = await self.get_profile(user_id)
        name = (data.get("name") or "").strip()
        if not name:
            raise ValidationError("Certification name is required.")
        if await self.certification_repo.exists_by_name(profile.id, name):
            raise ConflictError(f"Duplicate certification. '{name}' is already in your certifications list.")
        cert = Certification(profile_id=profile.id, **data)
        created = await self.certification_repo.create(cert)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("CERTIFICATION_ADDED", user_id=user_id, entity="certification", outcome="success")
        return created

    async def update_certification(self, user_id: uuid.UUID, certification_id: uuid.UUID, data: dict) -> Certification:
        profile = await self.get_profile(user_id)
        cert = await self.certification_repo.get_by_id(certification_id)
        if not cert or cert.profile_id != profile.id:
            raise NotFoundError("Certification not found.")
        if "name" in data:
            name = (data["name"] or "").strip()
            if not name:
                raise ValidationError("Certification name is required.")
            if await self.certification_repo.exists_by_name(profile.id, name) and name.lower() != cert.name.lower():
                raise ConflictError(f"Duplicate certification. '{name}' is already in your certifications list.")
            data["name"] = name
        for key, value in data.items():
            if value is not None:
                setattr(cert, key, value)
        await self.certification_repo.update(cert)
        await self.audit_service.log(
            "CERTIFICATION_UPDATED", user_id=user_id, entity="certification", outcome="success"
        )
        return cert

    async def delete_certification(self, user_id: uuid.UUID, certification_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        cert = await self.certification_repo.get_by_id(certification_id)
        if not cert or cert.profile_id != profile.id:
            raise NotFoundError("Certification not found.")
        await self.certification_repo.delete(cert)
        await self._recalculate_completeness(profile)
        await self.audit_service.log(
            "CERTIFICATION_DELETED", user_id=user_id, entity="certification", outcome="success"
        )

    # ── Languages ──

    async def add_language(self, user_id: uuid.UUID, data: dict) -> Language:
        profile = await self.get_profile(user_id)
        language = (data.get("language") or "").strip().title()
        if not language:
            raise ValidationError("Language name is required.")
        if await self.language_repo.exists_by_language(profile.id, language):
            raise ConflictError(f"Duplicate language. '{language}' is already in your languages list.")
        data["language"] = language
        lang = Language(profile_id=profile.id, **data)
        created = await self.language_repo.create(lang)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("LANGUAGE_ADDED", user_id=user_id, entity="language", outcome="success")
        return created

    async def update_language(self, user_id: uuid.UUID, language_id: uuid.UUID, data: dict) -> Language:
        profile = await self.get_profile(user_id)
        lang = await self.language_repo.get_by_id(language_id)
        if not lang or lang.profile_id != profile.id:
            raise NotFoundError("Language not found.")
        if "language" in data:
            language = (data["language"] or "").strip().title()
            if not language:
                raise ValidationError("Language name is required.")
            if await self.language_repo.exists_by_language(profile.id, language) and language.lower() != lang.language.lower():
                raise ConflictError(f"Duplicate language. '{language}' is already in your languages list.")
            data["language"] = language
        for key, value in data.items():
            if value is not None:
                setattr(lang, key, value)
        await self.language_repo.update(lang)
        await self.audit_service.log("LANGUAGE_UPDATED", user_id=user_id, entity="language", outcome="success")
        return lang

    async def delete_language(self, user_id: uuid.UUID, language_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        lang = await self.language_repo.get_by_id(language_id)
        if not lang or lang.profile_id != profile.id:
            raise NotFoundError("Language not found.")
        await self.language_repo.delete(lang)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("LANGUAGE_DELETED", user_id=user_id, entity="language", outcome="success")

    # ── Social Links ──

    async def add_social_link(self, user_id: uuid.UUID, data: dict) -> SocialLink:
        profile = await self.get_profile(user_id)
        platform = (data.get("platform") or "").strip().lower().replace(" ", "")
        if not platform:
            raise ValidationError("Platform is required.")
        if await self.social_link_repo.exists_by_platform(profile.id, platform):
            raise ConflictError(f"Duplicate social link. '{platform}' is already linked in your profile.")
        data["platform"] = platform
        link = SocialLink(profile_id=profile.id, **data)
        created = await self.social_link_repo.create(link)
        await self._recalculate_completeness(profile)
        await self.audit_service.log("SOCIAL_LINK_ADDED", user_id=user_id, entity="social_link", outcome="success")
        return created

    async def update_social_link(self, user_id: uuid.UUID, link_id: uuid.UUID, data: dict) -> SocialLink:
        profile = await self.get_profile(user_id)
        link = await self.social_link_repo.get_by_id(link_id)
        if not link or link.profile_id != profile.id:
            raise NotFoundError("Social link not found.")
        if "platform" in data:
            platform = (data["platform"] or "").strip().lower().replace(" ", "")
            if not platform:
                raise ValidationError("Platform is required.")
            if await self.social_link_repo.exists_by_platform(profile.id, platform) and platform != link.platform:
                raise ConflictError(f"Duplicate social link. '{platform}' is already linked in your profile.")
            data["platform"] = platform
        for key, value in data.items():
            if value is not None:
                setattr(link, key, value)
        await self.social_link_repo.update(link)
        await self.audit_service.log("SOCIAL_LINK_UPDATED", user_id=user_id, entity="social_link", outcome="success")
        return link

    async def delete_social_link(self, user_id: uuid.UUID, link_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        link = await self.social_link_repo.get_by_id(link_id)
        if not link or link.profile_id != profile.id:
            raise NotFoundError("Social link not found.")
        await self.social_link_repo.delete(link)
        await self.audit_service.log("SOCIAL_LINK_DELETED", user_id=user_id, entity="social_link", outcome="success")

    # ── Achievements ──

    async def add_achievement(self, user_id: uuid.UUID, data: dict) -> Achievement:
        profile = await self.get_profile(user_id)
        title = (data.get("title") or "").strip()
        if not title:
            raise ValidationError("Achievement title is required.")
        if await self.achievement_repo.exists_by_title(profile.id, title):
            raise ConflictError(f"Duplicate achievement. '{title}' is already in your achievements list.")
        achievement = Achievement(profile_id=profile.id, **data)
        created = await self.achievement_repo.create(achievement)
        await self._recalculate_completeness(profile)
        await self.audit_service.log(
            "ACHIEVEMENT_ADDED", user_id=user_id, entity="achievement", outcome="success"
        )
        return created

    async def update_achievement(self, user_id: uuid.UUID, achievement_id: uuid.UUID, data: dict) -> Achievement:
        profile = await self.get_profile(user_id)
        achievement = await self.achievement_repo.get_by_id(achievement_id)
        if not achievement or achievement.profile_id != profile.id:
            raise NotFoundError("Achievement not found.")
        if "title" in data:
            title = (data["title"] or "").strip()
            if not title:
                raise ValidationError("Achievement title is required.")
            if (
                await self.achievement_repo.exists_by_title(profile.id, title)
                and title.lower() != achievement.title.lower()
            ):
                raise ConflictError(f"Duplicate achievement. '{title}' is already in your achievements list.")
            data["title"] = title
        for key, value in data.items():
            if value is not None:
                setattr(achievement, key, value)
        await self.achievement_repo.update(achievement)
        await self.audit_service.log(
            "ACHIEVEMENT_UPDATED", user_id=user_id, entity="achievement", outcome="success"
        )
        return achievement

    async def delete_achievement(self, user_id: uuid.UUID, achievement_id: uuid.UUID) -> None:
        profile = await self.get_profile(user_id)
        achievement = await self.achievement_repo.get_by_id(achievement_id)
        if not achievement or achievement.profile_id != profile.id:
            raise NotFoundError("Achievement not found.")
        await self.achievement_repo.delete(achievement)
        await self._recalculate_completeness(profile)
        await self.audit_service.log(
            "ACHIEVEMENT_DELETED", user_id=user_id, entity="achievement", outcome="success"
        )

    # ── Validation helpers ──

    @staticmethod
    def _validate_dates(data: dict, current_field: str, entity: str) -> dict:
        start = data.get("start_date")
        end = data.get("end_date")
        is_current = data.get(current_field) is True
        if start is not None and not isinstance(start, date):
            raise ValidationError(f"Invalid start date for {entity}.")
        if end is not None and not isinstance(end, date):
            raise ValidationError(f"Invalid end date for {entity}.")
        if is_current and end is not None:
            raise ValidationError(f"End date must be empty when this is your current {entity.replace('experience', 'job')}.")
        if start is not None and end is not None and end < start:
            raise ValidationError("End date must be on or after the start date.")
        return data

    # ── Profile Completeness ──

    async def calculate_completeness(self, user_id: uuid.UUID) -> dict:
        profile = await self.profile_repo.get_by_user(user_id, load_relations=True)
        if not profile:
            profile = CareerProfile(user_id=user_id)
            profile = await self.profile_repo.create(profile)
            profile = await self.profile_repo.get_by_user(user_id, load_relations=True)
        counts = self._build_counts(profile)
        breakdown, percentage, missing = self._compute_completeness(profile, counts)
        return {"percentage": percentage, "breakdown": breakdown, "missing_sections": missing}

    async def _recalculate_completeness(self, profile: CareerProfile) -> None:
        profile = await self.profile_repo.get_by_user(profile.user_id, load_relations=True)
        if not profile:
            return
        counts = self._build_counts(profile)
        breakdown, percentage, missing = self._compute_completeness(profile, counts)
        profile.profile_completeness = percentage
        await self.profile_repo.update(profile)

    @staticmethod
    def _build_counts(profile: CareerProfile) -> dict[str, int]:
        return {
            "education": len(profile.education),
            "experience": len(profile.experience),
            "skills": len(profile.skills),
            "projects": len(profile.projects),
            "certifications": len(profile.certifications),
            "languages": len(profile.languages),
            "achievements": len(profile.achievements),
        }

    @staticmethod
    def _compute_completeness(profile: CareerProfile, counts: dict[str, int]) -> tuple[dict[str, int], int, list[str]]:
        weights = {
            "headline": 5,
            "professional_summary": 8,
            "total_years_experience": 5,
            "current_role": 5,
            "desired_role": 5,
            "employment_status": 3,
            "current_salary": 3,
            "expected_salary": 3,
            "salary_preference": 3,
            "willing_to_relocate": 2,
            "notice_period": 2,
            "portfolio_url": 3,
            "linkedin_url": 2,
            "github_url": 2,
            "website_url": 3,
            "education": 8,
            "experience": 8,
            "skills": 8,
            "projects": 4,
            "certifications": 4,
            "languages": 4,
            "achievements": 5,
            "social_links": 5,
        }
        breakdown: dict[str, int] = {}
        missing: list[str] = []

        for field, weight in weights.items():
            if field in counts:
                score = weight if counts[field] > 0 else 0
            elif field == "salary_preference":
                has_preference = (
                    profile.salary_preference is not None or profile.expected_salary is not None
                )
                score = weight if has_preference else 0
            elif field == "social_links":
                has_social = any(
                    [
                        profile.linkedin_url,
                        profile.github_url,
                        profile.portfolio_url,
                        profile.website_url,
                    ]
                ) or len(profile.social_links or []) > 0
                score = weight if has_social else 0
            else:
                score = weight if getattr(profile, field, None) is not None else 0

            breakdown[field] = score
            if score == 0:
                missing.append(field)

        total_weight = sum(weights.values())
        earned = sum(breakdown.values())
        percentage = int((earned / total_weight) * 100) if total_weight > 0 else 0
        percentage = max(0, min(100, percentage))

        return breakdown, percentage, missing
