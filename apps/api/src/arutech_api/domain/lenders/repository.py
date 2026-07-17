import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.lenders.entities import LenderEntity, LenderType


class LenderRepository(ABC):
    @abstractmethod
    async def create(self, lender: LenderEntity) -> LenderEntity: ...

    @abstractmethod
    async def get_by_id(self, lender_id: uuid.UUID) -> LenderEntity | None: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> LenderEntity | None: ...

    @abstractmethod
    async def list_lenders(
        self,
        *,
        type: LenderType | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LenderEntity]: ...

    @abstractmethod
    async def update(self, lender: LenderEntity) -> LenderEntity:
        """A full-entity update, like `LoanApplicationRepository`'s
        (Phase 7) — editing a lender's contact details and commission
        rate together in one form is the common case, not a series of
        single-field changes."""
        ...

    @abstractmethod
    async def set_active(self, lender_id: uuid.UUID, *, is_active: bool) -> LenderEntity: ...
