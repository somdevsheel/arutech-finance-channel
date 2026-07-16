import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.leads.entities import LeadEntity, LeadStatus
from arutech_api.domain.leads.repository import LeadRepository
from arutech_api.infrastructure.database.models.leads import Lead


def _to_entity(model: Lead) -> LeadEntity:
    return LeadEntity(
        id=model.id,
        contact_submission_id=model.contact_submission_id,
        name=model.name,
        email=model.email,
        phone=model.phone,
        status=model.status,
        score=model.score,
        assigned_to=model.assigned_to,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyLeadRepository(LeadRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, lead: LeadEntity) -> LeadEntity:
        model = Lead(
            id=lead.id,
            contact_submission_id=lead.contact_submission_id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            status=lead.status,
            score=lead.score,
            assigned_to=lead.assigned_to,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, lead_id: uuid.UUID) -> LeadEntity | None:
        result = await self._session.execute(select(Lead).where(Lead.id == lead_id))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list(
        self,
        *,
        status: LeadStatus | None = None,
        assigned_to: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeadEntity]:
        query = select(Lead)
        if status is not None:
            query = query.where(Lead.status == status)
        if assigned_to is not None:
            query = query.where(Lead.assigned_to == assigned_to)
        query = (
            query.order_by(Lead.score.desc(), Lead.created_at.desc()).limit(limit).offset(offset)
        )
        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def _get_model_or_raise(self, lead_id: uuid.UUID) -> Lead:
        result = await self._session.execute(select(Lead).where(Lead.id == lead_id))
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError("Lead not found")
        return model

    async def update_status(self, lead_id: uuid.UUID, status: LeadStatus) -> LeadEntity:
        model = await self._get_model_or_raise(lead_id)
        model.status = status
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def assign(self, lead_id: uuid.UUID, assignee_id: uuid.UUID) -> LeadEntity:
        model = await self._get_model_or_raise(lead_id)
        model.assigned_to = assignee_id
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
