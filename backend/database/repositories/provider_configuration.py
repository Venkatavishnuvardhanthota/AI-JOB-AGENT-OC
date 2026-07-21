from sqlalchemy import select

from database.models.provider_configuration import ProviderConfiguration
from database.repositories.base import BaseRepository


class ProviderConfigurationRepository(BaseRepository):
    model_class = ProviderConfiguration

    async def get_by_provider_name(self, provider_name: str) -> ProviderConfiguration | None:
        stmt = select(ProviderConfiguration).where(ProviderConfiguration.provider_name == provider_name)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_enabled(self) -> list[ProviderConfiguration]:
        stmt = select(ProviderConfiguration).where(ProviderConfiguration.is_enabled.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_type(self, provider_type: str) -> list[ProviderConfiguration]:
        stmt = select(ProviderConfiguration).where(ProviderConfiguration.provider_type == provider_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
