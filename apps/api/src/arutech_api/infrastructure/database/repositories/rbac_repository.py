import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.rbac.entities import PermissionEntity, RoleEntity
from arutech_api.domain.rbac.repository import RbacRepository
from arutech_api.infrastructure.database.models.rbac import (
    Permission,
    Role,
    role_permissions,
    user_roles,
)


def _role_to_entity(model: Role) -> RoleEntity:
    return RoleEntity(
        id=model.id, name=model.name, description=model.description, is_system=model.is_system
    )


def _permission_to_entity(model: Permission) -> PermissionEntity:
    return PermissionEntity(id=model.id, code=model.code, description=model.description)


class SqlAlchemyRbacRepository(RbacRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_user_permission_codes(self, user_id: uuid.UUID) -> set[str]:
        result = await self._session.execute(
            select(Permission.code)
            .join(Permission.roles)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
        )
        return set(result.scalars().all())

    async def get_user_roles(self, user_id: uuid.UUID) -> list[RoleEntity]:
        result = await self._session.execute(
            select(Role)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
        )
        return [_role_to_entity(model) for model in result.scalars().all()]

    async def get_role_by_name(self, name: str) -> RoleEntity | None:
        result = await self._session.execute(select(Role).where(Role.name == name))
        model = result.scalar_one_or_none()
        return _role_to_entity(model) if model else None

    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        existing = await self._session.execute(
            select(user_roles.c.user_id).where(
                user_roles.c.user_id == user_id, user_roles.c.role_id == role_id
            )
        )
        if existing.scalar_one_or_none() is not None:
            return
        await self._session.execute(user_roles.insert().values(user_id=user_id, role_id=role_id))

    async def remove_role_from_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        await self._session.execute(
            user_roles.delete().where(
                user_roles.c.user_id == user_id, user_roles.c.role_id == role_id
            )
        )

    async def get_role_by_id(self, role_id: uuid.UUID) -> RoleEntity | None:
        model = await self._session.get(Role, role_id)
        return _role_to_entity(model) if model else None

    async def list_roles(self) -> list[RoleEntity]:
        result = await self._session.execute(select(Role).order_by(Role.name))
        return [_role_to_entity(model) for model in result.scalars().all()]

    async def create_role(self, name: str, description: str) -> RoleEntity:
        model = Role(name=name, description=description, is_system=False)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _role_to_entity(model)

    async def delete_role(self, role_id: uuid.UUID) -> None:
        model = await self._session.get(Role, role_id)
        if model is None:
            raise NotFoundError(f"Role {role_id} not found")
        await self._session.delete(model)
        await self._session.flush()

    async def list_permissions(self) -> list[PermissionEntity]:
        result = await self._session.execute(select(Permission).order_by(Permission.code))
        return [_permission_to_entity(model) for model in result.scalars().all()]

    async def get_permission_by_code(self, code: str) -> PermissionEntity | None:
        result = await self._session.execute(select(Permission).where(Permission.code == code))
        model = result.scalar_one_or_none()
        return _permission_to_entity(model) if model else None

    async def get_role_permissions(self, role_id: uuid.UUID) -> list[PermissionEntity]:
        result = await self._session.execute(
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == role_id)
            .order_by(Permission.code)
        )
        return [_permission_to_entity(model) for model in result.scalars().all()]

    async def grant_permission_to_role(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        existing = await self._session.execute(
            select(role_permissions.c.role_id).where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return
        await self._session.execute(
            role_permissions.insert().values(role_id=role_id, permission_id=permission_id)
        )

    async def revoke_permission_from_role(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            role_permissions.delete().where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id,
            )
        )
