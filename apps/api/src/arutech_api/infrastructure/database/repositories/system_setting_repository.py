from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.settings.entities import SystemSettingEntity
from arutech_api.domain.settings.repository import SystemSettingRepository
from arutech_api.infrastructure.database.models.settings import SystemSetting


def _to_entity(model: SystemSetting) -> SystemSettingEntity:
    return SystemSettingEntity(
        id=model.id,
        key=model.key,
        value=model.value,
        value_type=model.value_type,
        description=model.description,
        updated_at=model.updated_at,
    )


class SqlAlchemySystemSettingRepository(SystemSettingRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_key(self, key: str) -> SystemSettingEntity | None:
        result = await self._session.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_settings(self) -> list[SystemSettingEntity]:
        result = await self._session.execute(select(SystemSetting).order_by(SystemSetting.key))
        return [_to_entity(model) for model in result.scalars().all()]

    async def set_value(self, key: str, value: str) -> SystemSettingEntity:
        result = await self._session.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError(f"Setting '{key}' not found")
        model.value = value
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
