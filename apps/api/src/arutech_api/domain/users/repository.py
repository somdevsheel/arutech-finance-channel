import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.users.entities import UserEntity, UserRole


class UserRepository(ABC):
    """Port the service layer depends on. Phase 1 ships a single SQLAlchemy
    adapter (`infrastructure.database.repositories.SqlAlchemyUserRepository`);
    swapping persistence later (e.g. a read-replica-aware implementation)
    means adding a new adapter here, not touching callers."""

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> UserEntity | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> UserEntity | None: ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool: ...

    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity: ...

    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity: ...

    @abstractmethod
    async def list_by_role(self, role: UserRole, *, active_only: bool = True) -> list[UserEntity]:
        """Phase 5 uses this to find candidate employees for lead
        auto-assignment; kept general (any role, optional active filter)
        since it's a reasonable thing later phases will also need."""
        ...

    @abstractmethod
    async def count_by_role(self, role: UserRole, *, active_only: bool = True) -> int:
        """A `COUNT(*)` sibling of `list_by_role` for Phase 8's "Employees"
        KPI, which only needs a number — loading every employee row into
        memory just to call `len()` would be wasteful."""
        ...
