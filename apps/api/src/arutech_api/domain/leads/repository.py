import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.leads.entities import LeadEntity, LeadStatus


class LeadRepository(ABC):
    @abstractmethod
    async def create(self, lead: LeadEntity) -> LeadEntity: ...

    @abstractmethod
    async def get_by_id(self, lead_id: uuid.UUID) -> LeadEntity | None: ...

    @abstractmethod
    async def list(
        self,
        *,
        status: LeadStatus | None = None,
        assigned_to: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeadEntity]: ...

    @abstractmethod
    async def update_status(self, lead_id: uuid.UUID, status: LeadStatus) -> LeadEntity: ...

    @abstractmethod
    async def assign(self, lead_id: uuid.UUID, assignee_id: uuid.UUID) -> LeadEntity: ...
