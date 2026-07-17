import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.loans.entities import (
    LoanAnalyticsSummary,
    LoanApplicationEntity,
    LoanApplicationStatus,
)


class LoanApplicationRepository(ABC):
    @abstractmethod
    async def create(self, application: LoanApplicationEntity) -> LoanApplicationEntity: ...

    @abstractmethod
    async def get_by_id(self, application_id: uuid.UUID) -> LoanApplicationEntity | None: ...

    @abstractmethod
    async def list_applications(
        self,
        *,
        status: LoanApplicationStatus | None = None,
        assigned_to: uuid.UUID | None = None,
        customer_user_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LoanApplicationEntity]: ...

    @abstractmethod
    async def update(self, application: LoanApplicationEntity) -> LoanApplicationEntity:
        """A full-entity update — unlike Lead/CustomerProfile's narrow
        per-field repository methods, an application has too many fields
        that change together in a single business action (e.g. sanction
        sets amount + tenure + date all at once) for per-field setters to
        stay readable. The service layer is the only caller, and always
        passes a `dataclasses.replace()`'d copy of an entity it just read
        — never a partial/blind overwrite."""
        ...

    @abstractmethod
    async def get_analytics_summary(self) -> LoanAnalyticsSummary: ...

    @abstractmethod
    async def get_hourly_activity_counts(self) -> dict[tuple[int, int], int]:
        """Application creation counts bucketed by (day_of_week, hour),
        day_of_week 0=Sunday..6=Saturday — mirrors
        `LeadRepository.get_hourly_activity_counts`, the other half of
        Phase 8's activity heatmap."""
        ...
