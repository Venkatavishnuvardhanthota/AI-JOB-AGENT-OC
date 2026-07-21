import uuid

from sqlalchemy import select

from database.models.saved_search import SavedSearch
from database.repositories.base import BaseRepository


class SavedSearchRepository(BaseRepository):
    model_class = SavedSearch

    async def list_by_user(self, user_id: uuid.UUID) -> list[SavedSearch]:
        stmt = select(SavedSearch).where(SavedSearch.user_id == user_id).order_by(SavedSearch.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
