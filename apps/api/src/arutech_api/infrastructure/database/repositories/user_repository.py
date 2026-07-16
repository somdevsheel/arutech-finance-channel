import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.users.entities import UserEntity
from arutech_api.domain.users.repository import UserRepository
from arutech_api.infrastructure.database.models.user import User


def _to_entity(model: User) -> UserEntity:
    return UserEntity(
        id=model.id,
        email=model.email,
        hashed_password=model.hashed_password,
        full_name=model.full_name,
        phone=model.phone,
        role=model.role,
        is_active=model.is_active,
        is_verified=model.is_verified,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserEntity | None:
        model = await self._session.get(User, user_id)
        return _to_entity(model) if model else None

    async def get_by_email(self, email: str) -> UserEntity | None:
        result = await self._session.execute(select(User).where(User.email == email))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def exists_by_email(self, email: str) -> bool:
        result = await self._session.execute(select(User.id).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def create(self, user: UserEntity) -> UserEntity:
        model = User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, user: UserEntity) -> UserEntity:
        model = await self._session.get(User, user.id)
        if model is None:
            raise NotFoundError(f"User {user.id} not found")

        model.email = user.email
        model.hashed_password = user.hashed_password
        model.full_name = user.full_name
        model.phone = user.phone
        model.role = user.role
        model.is_active = user.is_active
        model.is_verified = user.is_verified

        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
