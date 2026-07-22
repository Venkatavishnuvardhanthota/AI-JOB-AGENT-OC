import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.audit import AuditService
from database.models.career_profile import CareerProfile
from database.models.certification import Certification
from database.models.education import Education
from database.models.experience import Experience
from database.models.language import Language
from database.models.project import Project
from database.models.skill import Skill
from database.models.social_link import SocialLink
from database.repositories import (
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

    # ── Projects ──

    async def add_project(self, user_id: uuid.UUID, data: dict) -> Project:
        profile = await self.get_profile(user_id)
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
        link = SocialLink(profile_id=profile.id, **data)
        created = await self.social_link_repo.create(link)
        await self.audit_service.log("SOCIAL_LINK_ADDED", user_id=user_id, entity="social_link", outcome="success")
        return created

    async def update_social_link(self, user_id: uuid.UUID, link_id: uuid.UUID, data: dict) -> SocialLink:
        profile = await self.get_profile(user_id)
        link = await self.social_link_repo.get_by_id(link_id)
        if not link or link.profile_id != profile.id:
            raise NotFoundError("Social link not found.")
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

    # ── Profile Completeness ──

    async def calculate_completeness(self, user_id: uuid.UUID) -> dict:
        profile = await self.profile_repo.get_by_user(user_id, load_relations=True)
        if not profile:
            profile = CareerProfile(user_id=user_id)
            profile = await self.profile_repo.create(profile)
            profile = await self.profile_repo.get_by_user(user_id, load_relations=True)
        counts = {
            "education": len(profile.education),
            "experience": len(profile.experience),
            "skills": len(profile.skills),
            "projects": len(profile.projects),
            "certifications": len(profile.certifications),
            "languages": len(profile.languages),
        }
        breakdown, percentage, missing = self._compute_completeness(profile, counts)
        return {"percentage": percentage, "breakdown": breakdown, "missing_sections": missing}

    async def _recalculate_completeness(self, profile: CareerProfile) -> None:
        profile = await self.profile_repo.get_by_user(profile.user_id, load_relations=True)
        if not profile:
            return
        counts = {
            "education": len(profile.education),
            "experience": len(profile.experience),
            "skills": len(profile.skills),
            "projects": len(profile.projects),
            "certifications": len(profile.certifications),
            "languages": len(profile.languages),
        }
        breakdown, percentage, missing = self._compute_completeness(profile, counts)
        profile.profile_completeness = percentage
        await self.profile_repo.update(profile)

    @staticmethod
    def _compute_completeness(
        profile: CareerProfile, counts: dict[str, int]
    ) -> tuple[dict[str, int], int, list[str]]:
        weights = {
            "headline": 5,
            "professional_summary": 10,
            "total_years_experience": 5,
            "current_role": 5,
            "desired_role": 5,
            "employment_status": 3,
            "current_salary": 3,
            "expected_salary": 3,
            "willing_to_relocate": 2,
            "notice_period": 2,
            "portfolio_url": 3,
            "linkedin_url": 3,
            "github_url": 3,
            "website_url": 3,
            "education": 10,
            "experience": 10,
            "skills": 10,
            "projects": 5,
            "certifications": 5,
            "languages": 5,
        }
        breakdown: dict[str, int] = {}
        missing: list[str] = []

        for field, weight in weights.items():
            if field in counts:
                score = weight if counts[field] > 0 else 0
            else:
                score = weight if getattr(profile, field, None) else 0

            breakdown[field] = score
            if score == 0:
                missing.append(field)

        total_weight = sum(weights.values())
        earned = sum(breakdown.values())
        percentage = int((earned / total_weight) * 100) if total_weight > 0 else 0

        return breakdown, percentage, missing
