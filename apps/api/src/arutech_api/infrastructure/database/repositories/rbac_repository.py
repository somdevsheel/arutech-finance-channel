import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.domain.rbac.entities import RoleEntity
from arutech_api.domain.rbac.repository import RbacRepository
from arutech_api.infrastructure.database.models.rbac import Permission, Role, user_roles


def _role_to_entity(model: Role) -> RoleEntity:
    return RoleEntity(
        id=model.id, name=model.name, description=model.description, is_system=model.is_system
    )


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
