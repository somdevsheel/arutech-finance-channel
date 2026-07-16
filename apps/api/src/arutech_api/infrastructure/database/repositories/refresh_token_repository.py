import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.domain.auth.entities import RefreshTokenEntity
from arutech_api.domain.auth.repository import RefreshTokenRepository
from arutech_api.infrastructure.database.models.auth import RefreshToken


def _to_entity(model: RefreshToken) -> RefreshTokenEntity:
    return RefreshTokenEntity(
        id=model.id,
        user_id=model.user_id,
        jti=model.jti,
        token_hash=model.token_hash,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
        user_agent=model.user_agent,
        ip_address=model.ip_address,
        created_at=model.created_at,
    )


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, token: RefreshTokenEntity) -> RefreshTokenEntity:
        model = RefreshToken(
            id=token.id,
            user_id=token.user_id,
            jti=token.jti,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            user_agent=token.user_agent,
            ip_address=token.ip_address,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_jti(self, jti: str) -> RefreshTokenEntity | None:
        result = await self._session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_active_for_user(self, user_id: uuid.UUID) -> list[RefreshTokenEntity]:
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .where(RefreshToken.expires_at > now)
            .order_by(RefreshToken.created_at.desc())
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def revoke(self, token_id: uuid.UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked_at=datetime.now(UTC))
        )

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
