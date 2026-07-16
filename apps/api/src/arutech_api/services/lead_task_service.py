import uuid
from datetime import datetime

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.leads.entities import LeadTaskEntity, LeadTaskStatus
from arutech_api.domain.leads.repository import LeadRepository
from arutech_api.domain.leads.task_repository import LeadTaskRepository
from arutech_api.domain.users.entities import UserRole
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService


class LeadTaskService:
    """Covers project.md's "Follow-up Scheduling", "Tasks", and
    "Reminders" as one mechanism — see LeadTaskEntity's docstring for why
    these were never three separate systems to begin with."""

    def __init__(
        self,
        task_repo: LeadTaskRepository,
        lead_repo: LeadRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
    ):
        self._task_repo = task_repo
        self._lead_repo = lead_repo
        self._user_repo = user_repo
        self._audit_service = audit_service

    async def create_task(
        self,
        *,
        lead_id: uuid.UUID,
        title: str,
        due_at: datetime,
        assigned_to: uuid.UUID,
        notes: str | None,
        actor_id: uuid.UUID,
    ) -> LeadTaskEntity:
        lead = await self._lead_repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError("Lead not found")

        assignee = await self._user_repo.get_by_id(assigned_to)
        if assignee is None:
            raise NotFoundError("Assignee not found")
        if assignee.role not in (UserRole.EMPLOYEE, UserRole.ADMIN):
            raise ConflictError("Follow-up tasks can only be assigned to employees or admins")

        task = await self._task_repo.create(
            LeadTaskEntity(
                lead_id=lead_id, title=title, due_at=due_at, assigned_to=assigned_to, notes=notes
            )
        )
        await self._audit_service.record(
            action="lead.task_created",
            entity_type="lead",
            entity_id=str(lead_id),
            actor_id=actor_id,
            metadata={"task_id": str(task.id), "assigned_to": str(assigned_to)},
        )
        return task

    async def list_for_lead(self, lead_id: uuid.UUID) -> list[LeadTaskEntity]:
        lead = await self._lead_repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError("Lead not found")
        return await self._task_repo.list_for_lead(lead_id)

    async def list_for_assignee(
        self,
        assignee_id: uuid.UUID,
        *,
        status: LeadTaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeadTaskEntity]:
        return await self._task_repo.list_for_assignee(
            assignee_id, status=status, limit=limit, offset=offset
        )

    async def complete_task(self, task_id: uuid.UUID, *, actor_id: uuid.UUID) -> LeadTaskEntity:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")

        updated = await self._task_repo.mark_status(task_id, LeadTaskStatus.DONE)
        await self._audit_service.record(
            action="lead.task_completed",
            entity_type="lead",
            entity_id=str(task.lead_id),
            actor_id=actor_id,
            metadata={"task_id": str(task_id)},
        )
        return updated
