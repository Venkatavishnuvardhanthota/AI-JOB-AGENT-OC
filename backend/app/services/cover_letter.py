import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.cover_letter import CoverLetter
from app.repositories.cover_letter import CoverLetterRepository
from app.services.audit import AuditService


class CoverLetterService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CoverLetterRepository(session)
        self.audit_service = AuditService(session)

    async def generate(self, user_id: uuid.UUID, job_id: uuid.UUID, template: str = "professional") -> CoverLetter:
        cover_letter = CoverLetter(
            user_id=user_id,
            job_id=job_id,
            template=template,
        )
        created = await self.repo.create(cover_letter)
        await self.audit_service.log(
            "COVER_LETTER_GENERATED",
            user_id=user_id,
            entity="cover_letter",
            entity_id=created.id,
            outcome="success",
        )
        return created

    async def get(self, cover_letter_id: uuid.UUID) -> CoverLetter:
        cl = await self.repo.get_by_id(cover_letter_id)
        if not cl:
            raise NotFoundError("Cover letter not found.")
        return cl

    async def list_by_user(self, user_id: uuid.UUID) -> list[CoverLetter]:
        return await self.repo.list_by_user(user_id)
