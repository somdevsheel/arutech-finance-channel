import uuid

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.rbac.repository import RbacRepository
from arutech_api.domain.users.entities import UserEntity, UserRole
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService

# UserRole's four values happen to be named identically to the four
# seeded system roles (see seed_data.py) — a coarse role change (the
# portal a user lands in) stays synced with the fine-grained RBAC binding
# that actually drives their permissions, without a mapping table.
_SYSTEM_ROLE_NAMES = {role.value for role in UserRole}


class UserAdminService:
    """Phase 9's "User Management" — list/activate/deactivate/change-role
    on top of Phase 1's `User`. Doesn't touch registration, login, or
    password reset (Phase 2 owns those); this is the admin-facing view
    over accounts that already exist."""

    def __init__(
        self, user_repo: UserRepository, rbac_repo: RbacRepository, audit_service: AuditService
    ):
        self._user_repo = user_repo
        self._rbac_repo = rbac_repo
        self._audit_service = audit_service

    async def get_user(self, user_id: uuid.UUID) -> UserEntity:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def list_users(
        self,
        *,
        role: UserRole | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserEntity]:
        return await self._user_repo.list_users(
            role=role, is_active=is_active, limit=limit, offset=offset
        )

    async def set_active(
        self, user_id: uuid.UUID, *, is_active: bool, actor_id: uuid.UUID
    ) -> UserEntity:
        await self.get_user(user_id)  # 404s if unknown
        updated = await self._user_repo.set_active(user_id, is_active=is_active)
        await self._audit_service.record(
            action="user.activated" if is_active else "user.deactivated",
            entity_type="user",
            entity_id=str(user_id),
            actor_id=actor_id,
        )
        return updated

    async def set_role(
        self, user_id: uuid.UUID, role: UserRole, *, actor_id: uuid.UUID
    ) -> UserEntity:
        """Sets the coarse `role` column and re-syncs the RBAC system-role
        binding to match: removes whichever *system* role the user
        currently holds (if any) and assigns the one matching the new
        `role`. Any custom (non-system) roles Phase 9's Role Management
        separately granted are left untouched — this only owns the
        single system-role slot that mirrors `UserRole`."""
        await self.get_user(user_id)  # 404s if unknown

        current_roles = await self._rbac_repo.get_user_roles(user_id)
        for current in current_roles:
            if current.is_system and current.name in _SYSTEM_ROLE_NAMES:
                await self._rbac_repo.remove_role_from_user(user_id, current.id)

        new_system_role = await self._rbac_repo.get_role_by_name(role.value)
        if new_system_role is not None:
            await self._rbac_repo.assign_role_to_user(user_id, new_system_role.id)

        updated = await self._user_repo.set_role(user_id, role)
        await self._audit_service.record(
            action="user.role_changed",
            entity_type="user",
            entity_id=str(user_id),
            actor_id=actor_id,
            metadata={"role": role.value},
        )
        return updated
