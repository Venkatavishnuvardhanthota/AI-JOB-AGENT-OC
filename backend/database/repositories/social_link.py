import uuid

from sqlalchemy import select

from database.models.social_link import SocialLink
from database.repositories.base import BaseRepository


class SocialLinkRepository(BaseRepository):
    model_class = SocialLink

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[SocialLink]:
        stmt = (
            select(SocialLink)
            .where(SocialLink.profile_id == profile_id)
            .order_by(SocialLink.display_order.asc().nullslast(), SocialLink.platform)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_platform(self, profile_id: uuid.UUID, platform: str) -> bool:
        stmt = select(SocialLink).where(SocialLink.profile_id == profile_id, SocialLink.platform == platform)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none() is not None
