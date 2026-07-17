import uuid

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.rbac.entities import PermissionEntity, RoleEntity
from arutech_api.domain.rbac.repository import RbacRepository
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService


class RbacService:
    """Phase 9's "Role Management" and "Permission Management" — one
    service, since both operate on the same `roles`/`permissions`/
    `role_permissions` tables Phase 2 built and there's no legitimate
    read-only audience for this distinct from who can also manage it
    (unlike leads/customers/loans, this is internal admin configuration,
    not operational work); see docs/phase-9-architecture.md. Deliberately
    does *not* let an admin invent new permission *codes* — see
    `RbacRepository.list_permissions`'s docstring — only assign the
    existing, code-backed ones to roles."""

    def __init__(
        self, rbac_repo: RbacRepository, user_repo: UserRepository, audit_service: AuditService
    ):
        self._rbac_repo = rbac_repo
        self._user_repo = user_repo
        self._audit_service = audit_service

    async def list_roles(self) -> list[RoleEntity]:
        return await self._rbac_repo.list_roles()

    async def get_role(self, role_id: uuid.UUID) -> RoleEntity:
        role = await self._rbac_repo.get_role_by_id(role_id)
        if role is None:
            raise NotFoundError(f"Role {role_id} not found")
        return role

    async def get_role_permissions(self, role_id: uuid.UUID) -> list[PermissionEntity]:
        await self.get_role(role_id)  # 404s if unknown
        return await self._rbac_repo.get_role_permissions(role_id)

    async def create_role(self, name: str, description: str, *, actor_id: uuid.UUID) -> RoleEntity:
        existing = await self._rbac_repo.get_role_by_name(name)
        if existing is not None:
            raise ConflictError(f"A role named '{name}' already exists")
        role = await self._rbac_repo.create_role(name, description)
        await self._audit_service.record(
            action="role.created", entity_type="role", entity_id=str(role.id), actor_id=actor_id
        )
        return role

    async def delete_role(self, role_id: uuid.UUID, *, actor_id: uuid.UUID) -> None:
        role = await self.get_role(role_id)
        if role.is_system:
            raise ConflictError("System roles cannot be deleted")
        await self._rbac_repo.delete_role(role_id)
        await self._audit_service.record(
            action="role.deleted", entity_type="role", entity_id=str(role_id), actor_id=actor_id
        )

    async def list_permissions(self) -> list[PermissionEntity]:
        return await self._rbac_repo.list_permissions()

    async def grant_permission(
        self, role_id: uuid.UUID, permission_code: str, *, actor_id: uuid.UUID
    ) -> None:
        await self.get_role(role_id)  # 404s if unknown
        permission = await self._rbac_repo.get_permission_by_code(permission_code)
        if permission is None:
            raise NotFoundError(f"Unknown permission code '{permission_code}'")
        await self._rbac_repo.grant_permission_to_role(role_id, permission.id)
        await self._audit_service.record(
            action="role.permission_granted",
            entity_type="role",
            entity_id=str(role_id),
            actor_id=actor_id,
            metadata={"permission": permission_code},
        )

    async def revoke_permission(
        self, role_id: uuid.UUID, permission_code: str, *, actor_id: uuid.UUID
    ) -> None:
        await self.get_role(role_id)  # 404s if unknown
        permission = await self._rbac_repo.get_permission_by_code(permission_code)
        if permission is None:
            raise NotFoundError(f"Unknown permission code '{permission_code}'")
        await self._rbac_repo.revoke_permission_from_role(role_id, permission.id)
        await self._audit_service.record(
            action="role.permission_revoked",
            entity_type="role",
            entity_id=str(role_id),
            actor_id=actor_id,
            metadata={"permission": permission_code},
        )

    async def _get_user_or_raise(self, user_id: uuid.UUID) -> None:
        # user_roles.user_id is FK-constrained; without this check an
        # unknown user_id would surface as a raw IntegrityError (500)
        # instead of a clean 404.
        if await self._user_repo.get_by_id(user_id) is None:
            raise NotFoundError(f"User {user_id} not found")

    async def assign_role_to_user(
        self, role_id: uuid.UUID, user_id: uuid.UUID, *, actor_id: uuid.UUID
    ) -> None:
        await self.get_role(role_id)  # 404s if unknown
        await self._get_user_or_raise(user_id)
        await self._rbac_repo.assign_role_to_user(user_id, role_id)
        await self._audit_service.record(
            action="role.assigned_to_user",
            entity_type="role",
            entity_id=str(role_id),
            actor_id=actor_id,
            metadata={"user_id": str(user_id)},
        )

    async def remove_role_from_user(
        self, role_id: uuid.UUID, user_id: uuid.UUID, *, actor_id: uuid.UUID
    ) -> None:
        await self.get_role(role_id)  # 404s if unknown
        await self._get_user_or_raise(user_id)
        await self._rbac_repo.remove_role_from_user(user_id, role_id)
        await self._audit_service.record(
            action="role.removed_from_user",
            entity_type="role",
            entity_id=str(role_id),
            actor_id=actor_id,
            metadata={"user_id": str(user_id)},
        )
