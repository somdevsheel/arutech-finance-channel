import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.users.entities import UserEntity


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
