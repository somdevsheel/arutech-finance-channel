import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.rbac.entities import RoleEntity


class RbacRepository(ABC):
    @abstractmethod
    async def get_user_permission_codes(self, user_id: uuid.UUID) -> set[str]: ...

    @abstractmethod
    async def get_user_roles(self, user_id: uuid.UUID) -> list[RoleEntity]: ...

    @abstractmethod
    async def get_role_by_name(self, name: str) -> RoleEntity | None: ...

    @abstractmethod
    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None: ...
