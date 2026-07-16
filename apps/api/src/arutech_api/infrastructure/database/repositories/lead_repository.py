import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.leads.entities import (
    TERMINAL_STATUSES,
    LeadAnalyticsSummary,
    LeadEntity,
    LeadSource,
    LeadStatus,
)
from arutech_api.domain.leads.repository import LeadRepository
from arutech_api.infrastructure.database.models.leads import Lead


def _to_entity(model: Lead) -> LeadEntity:
    return LeadEntity(
        id=model.id,
        contact_submission_id=model.contact_submission_id,
        source=model.source,
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
            source=lead.source,
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

    async def list_leads(
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

    async def update_score(self, lead_id: uuid.UUID, score: int) -> LeadEntity:
        model = await self._get_model_or_raise(lead_id)
        model.score = score
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def assign(self, lead_id: uuid.UUID, assignee_id: uuid.UUID) -> LeadEntity:
        model = await self._get_model_or_raise(lead_id)
        model.assigned_to = assignee_id
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def find_active_duplicate(self, *, email: str, phone: str | None) -> LeadEntity | None:
        match_condition = (
            (Lead.email == email) | (Lead.phone == phone) if phone else Lead.email == email
        )
        query = select(Lead).where(Lead.status.notin_(TERMINAL_STATUSES), match_condition)
        result = await self._session.execute(query.order_by(Lead.created_at.desc()).limit(1))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def count_open_by_assignee(self, assignee_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not assignee_ids:
            return {}

        result = await self._session.execute(
            select(Lead.assigned_to, func.count(Lead.id))
            .where(
                Lead.assigned_to.in_(assignee_ids),
                Lead.status.notin_(TERMINAL_STATUSES),
            )
            .group_by(Lead.assigned_to)
        )
        counts = {assignee_id: 0 for assignee_id in assignee_ids}
        for assignee_id, count in result.all():
            counts[assignee_id] = count
        return counts

    async def get_analytics_summary(self) -> LeadAnalyticsSummary:
        total = (await self._session.execute(select(func.count(Lead.id)))).scalar_one()

        by_status_query = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
        by_status_rows = (await self._session.execute(by_status_query)).all()
        by_status: dict[LeadStatus, int] = {status: count for status, count in by_status_rows}

        by_source_query = select(Lead.source, func.count(Lead.id)).group_by(Lead.source)
        by_source_rows = (await self._session.execute(by_source_query)).all()
        by_source: dict[LeadSource, int] = {source: count for source, count in by_source_rows}

        average_score = (await self._session.execute(select(func.avg(Lead.score)))).scalar_one()

        converted = by_status.get(LeadStatus.CONVERTED, 0)
        conversion_rate = (converted / total) if total else 0.0

        return LeadAnalyticsSummary(
            total_leads=total,
            by_status=by_status,
            by_source=by_source,
            average_score=round(float(average_score), 2) if average_score is not None else 0.0,
            conversion_rate=round(conversion_rate, 4),
        )
