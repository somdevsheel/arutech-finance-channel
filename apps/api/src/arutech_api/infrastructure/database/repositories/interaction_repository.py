import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.domain.crm.entities import InteractionChannel, InteractionEntity
from arutech_api.domain.crm.interaction_repository import InteractionRepository
from arutech_api.infrastructure.database.models.crm import Interaction


def _to_entity(model: Interaction) -> InteractionEntity:
    return InteractionEntity(
        id=model.id,
        customer_user_id=model.customer_user_id,
        channel=model.channel,
        direction=model.direction,
        summary=model.summary,
        notes=model.notes,
        occurred_at=model.occurred_at,
        logged_by=model.logged_by,
        created_at=model.created_at,
    )


class SqlAlchemyInteractionRepository(InteractionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, interaction: InteractionEntity) -> InteractionEntity:
        model = Interaction(
            id=interaction.id,
            customer_user_id=interaction.customer_user_id,
            channel=interaction.channel,
            direction=interaction.direction,
            summary=interaction.summary,
            notes=interaction.notes,
            occurred_at=interaction.occurred_at,
            logged_by=interaction.logged_by,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def list_for_customer(
        self, customer_user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[InteractionEntity]:
        result = await self._session.execute(
            select(Interaction)
            .where(Interaction.customer_user_id == customer_user_id)
            .order_by(Interaction.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_channel_counts(self) -> dict[InteractionChannel, int]:
        result = await self._session.execute(
            select(Interaction.channel, func.count(Interaction.id)).group_by(Interaction.channel)
        )
        return {channel: count for channel, count in result.all()}
