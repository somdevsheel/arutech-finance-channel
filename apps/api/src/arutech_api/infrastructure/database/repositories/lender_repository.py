import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.lenders.entities import LenderEntity, LenderType
from arutech_api.domain.lenders.repository import LenderRepository
from arutech_api.infrastructure.database.models.lenders import Lender


def _to_entity(model: Lender) -> LenderEntity:
    return LenderEntity(
        id=model.id,
        name=model.name,
        type=model.type,
        code=model.code,
        contact_email=model.contact_email,
        contact_phone=model.contact_phone,
        commission_rate_percent=model.commission_rate_percent,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyLenderRepository(LenderRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, lender: LenderEntity) -> LenderEntity:
        model = Lender(
            id=lender.id,
            name=lender.name,
            type=lender.type,
            code=lender.code,
            contact_email=lender.contact_email,
            contact_phone=lender.contact_phone,
            commission_rate_percent=lender.commission_rate_percent,
            is_active=lender.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, lender_id: uuid.UUID) -> LenderEntity | None:
        model = await self._session.get(Lender, lender_id)
        return _to_entity(model) if model else None

    async def get_by_code(self, code: str) -> LenderEntity | None:
        result = await self._session.execute(select(Lender).where(Lender.code == code))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_lenders(
        self,
        *,
        type: LenderType | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LenderEntity]:
        query = select(Lender)
        if type is not None:
            query = query.where(Lender.type == type)
        if is_active is not None:
            query = query.where(Lender.is_active.is_(is_active))
        query = query.order_by(Lender.name).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def update(self, lender: LenderEntity) -> LenderEntity:
        model = await self._session.get(Lender, lender.id)
        if model is None:
            raise NotFoundError(f"Lender {lender.id} not found")

        model.name = lender.name
        model.type = lender.type
        model.code = lender.code
        model.contact_email = lender.contact_email
        model.contact_phone = lender.contact_phone
        model.commission_rate_percent = lender.commission_rate_percent
        model.is_active = lender.is_active

        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def set_active(self, lender_id: uuid.UUID, *, is_active: bool) -> LenderEntity:
        model = await self._session.get(Lender, lender_id)
        if model is None:
            raise NotFoundError(f"Lender {lender_id} not found")
        model.is_active = is_active
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
