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

    @abstractmethod
    async def list_users(
        self,
        *,
        role: UserRole | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserEntity]:
        """Phase 9's User Management listing — unlike `list_by_role`, both
        filters are optional (an admin browsing all users doesn't know a
        role in advance) and it's paginated, since this is the one place
        every user in the system can show up in a single list."""
        ...

    @abstractmethod
    async def set_active(self, user_id: uuid.UUID, *, is_active: bool) -> UserEntity:
        """Narrow setter (Lead/CustomerProfile's convention, not
        LoanApplication's full-entity `update()`) for Phase 9's
        activate/deactivate. A deactivated user can't log in (see
        `AuthService`) but keeps every historical record — leads they
        worked, applications they own — intact."""
        ...

    @abstractmethod
    async def set_role(self, user_id: uuid.UUID, role: UserRole) -> UserEntity:
        """Narrow setter for the coarse `UserRole` (the portal selector —
        see `UserEntity.role`'s docstring). The service layer keeps this
        in sync with the separate RBAC `roles`/`user_roles` tables; the
        repository only ever touches the one column."""
        ...
