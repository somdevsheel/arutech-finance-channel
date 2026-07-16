import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.security import hash_password, verify_password
from arutech_api.domain.users.entities import UserEntity, UserRole
from arutech_api.infrastructure.database.repositories.user_repository import (
    SqlAlchemyUserRepository,
)

pytestmark = pytest.mark.asyncio


async def test_create_and_fetch_user_by_id(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    user = UserEntity(
        email="ada@arutech.test",
        hashed_password=hash_password("s3cure-Passw0rd!"),
        full_name="Ada Lovelace",
    )

    created = await repo.create(user)
    await db_session.commit()

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.email == "ada@arutech.test"
    assert fetched.role == UserRole.CUSTOMER
    assert verify_password("s3cure-Passw0rd!", fetched.hashed_password)


async def test_get_by_email_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    assert await repo.get_by_email("nobody@arutech.test") is None


async def test_exists_by_email(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    await repo.create(
        UserEntity(
            email="grace@arutech.test",
            hashed_password=hash_password("another-Passw0rd!"),
            full_name="Grace Hopper",
        )
    )
    await db_session.commit()

    assert await repo.exists_by_email("grace@arutech.test") is True
    assert await repo.exists_by_email("nobody@arutech.test") is False


async def test_get_by_id_returns_none_for_unknown_id(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None
