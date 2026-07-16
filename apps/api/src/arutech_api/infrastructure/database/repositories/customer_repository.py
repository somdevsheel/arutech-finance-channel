import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.crm.entities import CustomerProfileEntity, CustomerSegment
from arutech_api.domain.crm.repository import CustomerRepository
from arutech_api.infrastructure.database.models.crm import CustomerProfile, Tag, customer_tags


def _to_entity(model: CustomerProfile) -> CustomerProfileEntity:
    return CustomerProfileEntity(
        id=model.id,
        user_id=model.user_id,
        relationship_manager_id=model.relationship_manager_id,
        segment=model.segment,
        tags=tuple(sorted(tag.name for tag in model.tags)),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyCustomerRepository(CustomerRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def _get_model(self, user_id: uuid.UUID) -> CustomerProfile | None:
        result = await self._session.execute(
            select(CustomerProfile).where(CustomerProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_profile(self, user_id: uuid.UUID) -> CustomerProfileEntity:
        model = await self._get_model(user_id)
        if model is None:
            model = CustomerProfile(user_id=user_id)
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
        return _to_entity(model)

    async def get_profile(self, user_id: uuid.UUID) -> CustomerProfileEntity | None:
        model = await self._get_model(user_id)
        return _to_entity(model) if model else None

    async def list_profiles(
        self,
        *,
        segment: CustomerSegment | None = None,
        tag: str | None = None,
        relationship_manager_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CustomerProfileEntity]:
        query = select(CustomerProfile)
        if segment is not None:
            query = query.where(CustomerProfile.segment == segment)
        if relationship_manager_id is not None:
            query = query.where(
                CustomerProfile.relationship_manager_id == relationship_manager_id
            )
        if tag is not None:
            query = (
                query.join(customer_tags, customer_tags.c.customer_profile_id == CustomerProfile.id)
                .join(Tag, Tag.id == customer_tags.c.tag_id)
                .where(Tag.name == tag)
            )
        query = query.order_by(CustomerProfile.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().unique().all()]

    async def set_relationship_manager(
        self, user_id: uuid.UUID, relationship_manager_id: uuid.UUID
    ) -> CustomerProfileEntity:
        model = await self._get_model(user_id)
        if model is None:
            raise NotFoundError("Customer profile not found")
        model.relationship_manager_id = relationship_manager_id
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def set_segment(
        self, user_id: uuid.UUID, segment: CustomerSegment
    ) -> CustomerProfileEntity:
        model = await self._get_model(user_id)
        if model is None:
            raise NotFoundError("Customer profile not found")
        model.segment = segment
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def _get_or_create_tag(self, name: str) -> Tag:
        result = await self._session.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = Tag(name=name)
            self._session.add(tag)
            await self._session.flush()
        return tag

    async def add_tag(self, user_id: uuid.UUID, tag_name: str) -> CustomerProfileEntity:
        model = await self._get_model(user_id)
        if model is None:
            raise NotFoundError("Customer profile not found")

        tag = await self._get_or_create_tag(tag_name)
        if tag not in model.tags:
            model.tags.append(tag)
            await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def remove_tag(self, user_id: uuid.UUID, tag_name: str) -> CustomerProfileEntity:
        model = await self._get_model(user_id)
        if model is None:
            raise NotFoundError("Customer profile not found")

        model.tags = [tag for tag in model.tags if tag.name != tag_name]
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def list_all_tags(self) -> list[str]:
        result = await self._session.execute(select(Tag.name).order_by(Tag.name))
        return list(result.scalars().all())

    async def count_total(self) -> int:
        result = await self._session.execute(select(func.count(CustomerProfile.id)))
        return result.scalar_one()

    async def count_by_segment(self) -> dict[CustomerSegment, int]:
        result = await self._session.execute(
            select(CustomerProfile.segment, func.count(CustomerProfile.id)).group_by(
                CustomerProfile.segment
            )
        )
        return {segment: count for segment, count in result.all()}

    async def count_without_relationship_manager(self) -> int:
        result = await self._session.execute(
            select(func.count(CustomerProfile.id)).where(
                CustomerProfile.relationship_manager_id.is_(None)
            )
        )
        return result.scalar_one()
