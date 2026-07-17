import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.rbac.entities import PermissionEntity, RoleEntity


class RbacRepository(ABC):
    @abstractmethod
    async def get_user_permission_codes(self, user_id: uuid.UUID) -> set[str]: ...

    @abstractmethod
    async def get_user_roles(self, user_id: uuid.UUID) -> list[RoleEntity]: ...

    @abstractmethod
    async def get_role_by_name(self, name: str) -> RoleEntity | None: ...

    @abstractmethod
    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def remove_role_from_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        """The complement `assign_role_to_user` never needed until Phase
        9's Role Management let an admin unassign a role directly (not
        just implicitly via `UserAdminService.set_role`'s system-role
        sync)."""
        ...

    @abstractmethod
    async def get_role_by_id(self, role_id: uuid.UUID) -> RoleEntity | None: ...

    @abstractmethod
    async def list_roles(self) -> list[RoleEntity]: ...

    @abstractmethod
    async def create_role(self, name: str, description: str) -> RoleEntity:
        """Always creates a custom (`is_system=False`) role — the four
        system roles are seeded once, by migration, and never created
        through this method; see `RbacService.create_role`."""
        ...

    @abstractmethod
    async def delete_role(self, role_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def list_permissions(self) -> list[PermissionEntity]:
        """Every permission *code* that exists — not what's assigned to any
        particular role. This is the fixed catalog `require_permission()`
        checks against; Phase 9 lets an admin see it and assign existing
        codes to roles, not invent new ones (a permission code with no
        `require_permission(code)` call behind it in the actual API would
        do nothing)."""
        ...

    @abstractmethod
    async def get_permission_by_code(self, code: str) -> PermissionEntity | None: ...

    @abstractmethod
    async def get_role_permissions(self, role_id: uuid.UUID) -> list[PermissionEntity]: ...

    @abstractmethod
    async def grant_permission_to_role(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        ...

    @abstractmethod
    async def revoke_permission_from_role(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None: ...
