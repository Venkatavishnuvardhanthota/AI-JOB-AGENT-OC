import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blacklisted_company import BlacklistedCompany
from app.models.certification import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.language import Language
from app.models.project import Project
from app.models.skill import Skill
from app.models.user_profile import UserProfile
from app.repositories.base import BaseRepository


class ProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_profile(self, user_id: uuid.UUID) -> UserProfile:
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.session.add(profile)
            await self.session.flush()
            await self.session.refresh(profile)
        return profile

    async def update_profile(
        self, user_id: uuid.UUID, **kwargs
    ) -> UserProfile:
        profile = await self.get_or_create_profile(user_id)
        for key, value in kwargs.items():
            if value is not None:
                setattr(profile, key, value)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    def get_repo(self, model) -> BaseRepository:
        return BaseRepository(model, self.session)

    async def get_educations(self, user_id: uuid.UUID):
        stmt = (
            select(Education)
            .where(Education.user_id == user_id)
            .order_by(Education.start_date.desc().nullslast())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_experiences(self, user_id: uuid.UUID):
        stmt = (
            select(Experience)
            .where(Experience.user_id == user_id)
            .order_by(Experience.start_date.desc().nullslast())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_projects(self, user_id: uuid.UUID):
        stmt = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.start_date.desc().nullslast())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_skills(self, user_id: uuid.UUID):
        stmt = select(Skill).where(Skill.user_id == user_id).order_by(Skill.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_certifications(self, user_id: uuid.UUID):
        stmt = (
            select(Certification)
            .where(Certification.user_id == user_id)
            .order_by(Certification.issue_date.desc().nullslast())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_languages(self, user_id: uuid.UUID):
        stmt = (
            select(Language)
            .where(Language.user_id == user_id)
            .order_by(Language.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_blacklisted_companies(self, user_id: uuid.UUID):
        stmt = (
            select(BlacklistedCompany)
            .where(BlacklistedCompany.user_id == user_id)
            .order_by(BlacklistedCompany.company_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
