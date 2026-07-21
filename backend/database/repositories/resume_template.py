import uuid

from sqlalchemy import select

from database.models.resume_template import ResumeTemplate
from database.repositories.base import BaseRepository


class ResumeTemplateRepository(BaseRepository):
    model_class = ResumeTemplate

    async def list_by_user(self, user_id: uuid.UUID) -> list[ResumeTemplate]:
        stmt = (
            select(ResumeTemplate)
            .where((ResumeTemplate.user_id == user_id) | (ResumeTemplate.is_public.is_(True)))
            .order_by(ResumeTemplate.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_default(self) -> ResumeTemplate | None:
        stmt = select(ResumeTemplate).where(ResumeTemplate.is_default.is_(True)).limit(1)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
