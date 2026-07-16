import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.leads.entities import LeadTaskEntity, LeadTaskStatus
from arutech_api.domain.leads.task_repository import LeadTaskRepository
from arutech_api.infrastructure.database.models.leads import LeadTask


def _to_entity(model: LeadTask) -> LeadTaskEntity:
    return LeadTaskEntity(
        id=model.id,
        lead_id=model.lead_id,
        title=model.title,
        notes=model.notes,
        due_at=model.due_at,
        assigned_to=model.assigned_to,
        status=model.status,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyLeadTaskRepository(LeadTaskRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, task: LeadTaskEntity) -> LeadTaskEntity:
        model = LeadTask(
            id=task.id,
            lead_id=task.lead_id,
            title=task.title,
            notes=task.notes,
            due_at=task.due_at,
            assigned_to=task.assigned_to,
            status=task.status,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, task_id: uuid.UUID) -> LeadTaskEntity | None:
        result = await self._session.execute(select(LeadTask).where(LeadTask.id == task_id))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_for_lead(self, lead_id: uuid.UUID) -> list[LeadTaskEntity]:
        result = await self._session.execute(
            select(LeadTask).where(LeadTask.lead_id == lead_id).order_by(LeadTask.due_at)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def list_for_assignee(
        self,
        assignee_id: uuid.UUID,
        *,
        status: LeadTaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeadTaskEntity]:
        query = select(LeadTask).where(LeadTask.assigned_to == assignee_id)
        if status is not None:
            query = query.where(LeadTask.status == status)
        query = query.order_by(LeadTask.due_at).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def mark_status(self, task_id: uuid.UUID, status: LeadTaskStatus) -> LeadTaskEntity:
        result = await self._session.execute(select(LeadTask).where(LeadTask.id == task_id))
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError("Task not found")

        model.status = status
        model.completed_at = datetime.now(UTC) if status == LeadTaskStatus.DONE else None
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
