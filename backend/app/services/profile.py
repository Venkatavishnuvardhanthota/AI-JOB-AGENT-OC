import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_profile import CareerProfile
from app.repositories.career_profile import CareerProfileRepository
from app.repositories.certification import CertificationRepository
from app.repositories.education import EducationRepository
from app.repositories.experience import ExperienceRepository
from app.repositories.job_preference import JobPreferenceRepository
from app.repositories.language import LanguageRepository
from app.repositories.project import ProjectRepository
from app.repositories.skill import SkillRepository
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
        self.preference_repo = JobPreferenceRepository(session)
        self.audit_service = AuditService(session)

    async def get_profile(self, user_id: uuid.UUID) -> CareerProfile:
        profile = await self.profile_repo.get_by_user(user_id)
        if not profile:
            profile = CareerProfile(user_id=user_id)
            profile = await self.profile_repo.create(profile)
        return profile

    async def update_profile(self, user_id: uuid.UUID, data: dict) -> CareerProfile:
        profile = await self.get_profile(user_id)
        for key, value in data.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)
        await self.profile_repo.update(profile)
        await self.audit_service.log("PROFILE_UPDATED", user_id=user_id, outcome="success")
        return profile

    async def calculate_completeness(self, user_id: uuid.UUID) -> dict:
        profile = await self.get_profile(user_id)
        sections = {
            "Personal Information": bool(profile.professional_summary),
            "Education": len(profile.education) > 0,
            "Experience": len(profile.experience) > 0,
            "Skills": len(profile.skills) > 0,
            "Projects": len(profile.projects) > 0,
            "Certifications": len(profile.certifications) > 0,
            "Languages": len(profile.languages) > 0,
        }
        filled = sum(1 for completed in sections.values() if completed)
        total = len(sections)
        percentage = int((filled / total) * 100) if total > 0 else 0
        missing = [name for name, completed in sections.items() if not completed]
        return {"percentage": percentage, "missing_sections": missing}
