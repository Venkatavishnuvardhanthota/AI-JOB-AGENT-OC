from sqlalchemy import select

from database.models.company import Company
from database.repositories.base import BaseRepository


class CompanyRepository(BaseRepository):
    model_class = Company

    async def get_by_name(self, name: str) -> Company | None:
        stmt = select(Company).where(Company.name == name)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def search_by_name(self, query: str, limit: int = 10) -> list[Company]:
        stmt = select(Company).where(Company.name.ilike(f"%{query}%")).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
