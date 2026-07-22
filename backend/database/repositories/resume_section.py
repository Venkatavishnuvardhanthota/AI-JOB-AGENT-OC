import uuid

from sqlalchemy import select

from database.models.resume_section import ResumeSection
from database.repositories.base import BaseRepository


class ResumeSectionRepository(BaseRepository):
    model_class = ResumeSection

    async def list_by_resume(self, resume_id: uuid.UUID) -> list[ResumeSection]:
        stmt = (
            select(ResumeSection)
            .where(ResumeSection.resume_id == resume_id)
            .order_by(ResumeSection.sort_order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_all_for_resume(self, resume_id: uuid.UUID) -> None:
        sections = await self.list_by_resume(resume_id)
        for section in sections:
            await self.session.delete(section)
