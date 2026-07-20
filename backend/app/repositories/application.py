import uuid

from sqlalchemy import func, select

from app.models.application import Application
from app.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository):
    model_class = Application

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        skip: int = 0,
        limit: int = 25,
    ) -> tuple[list[Application], int]:
        stmt = select(Application).where(Application.user_id == user_id)
        count_stmt = select(func.count()).where(Application.user_id == user_id)

        if status:
            stmt = stmt.where(Application.status == status)
            count_stmt = count_stmt.where(Application.status == status)

        stmt = stmt.offset(skip).limit(limit).order_by(Application.created_at.desc())
        result = await self.session.execute(stmt)
        apps = list(result.scalars().all())

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        return apps, total

    async def exists(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        stmt = select(Application).where(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
