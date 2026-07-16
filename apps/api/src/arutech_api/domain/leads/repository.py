import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.leads.entities import LeadAnalyticsSummary, LeadEntity, LeadStatus


class LeadRepository(ABC):
    @abstractmethod
    async def create(self, lead: LeadEntity) -> LeadEntity: ...

    @abstractmethod
    async def get_by_id(self, lead_id: uuid.UUID) -> LeadEntity | None: ...

    @abstractmethod
    async def list_leads(
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
    async def update_score(self, lead_id: uuid.UUID, score: int) -> LeadEntity: ...

    @abstractmethod
    async def assign(self, lead_id: uuid.UUID, assignee_id: uuid.UUID) -> LeadEntity: ...

    @abstractmethod
    async def find_active_duplicate(self, *, email: str, phone: str | None) -> LeadEntity | None:
        """A non-terminal-status lead already sharing this email or phone,
        if one exists — see `LeadService.create_from_contact_submission`
        for why terminal-status leads never count as duplicates."""
        ...

    @abstractmethod
    async def count_open_by_assignee(self, assignee_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        """How many non-terminal leads each given user currently owns —
        the input to least-loaded auto-assignment."""
        ...

    @abstractmethod
    async def get_analytics_summary(self) -> LeadAnalyticsSummary: ...
