import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.leads.entities import LeadTaskEntity, LeadTaskStatus


class LeadTaskRepository(ABC):
    @abstractmethod
    async def create(self, task: LeadTaskEntity) -> LeadTaskEntity: ...

    @abstractmethod
    async def get_by_id(self, task_id: uuid.UUID) -> LeadTaskEntity | None: ...

    @abstractmethod
    async def list_for_lead(self, lead_id: uuid.UUID) -> list[LeadTaskEntity]: ...

    @abstractmethod
    async def list_for_assignee(
        self,
        assignee_id: uuid.UUID,
        *,
        status: LeadTaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeadTaskEntity]: ...

    @abstractmethod
    async def mark_status(self, task_id: uuid.UUID, status: LeadTaskStatus) -> LeadTaskEntity: ...
