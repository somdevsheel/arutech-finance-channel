import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.domain.auth.entities import OtpEntity, OtpPurpose
from arutech_api.domain.auth.repository import OtpRepository
from arutech_api.infrastructure.database.models.auth import OtpCode


def _to_entity(model: OtpCode) -> OtpEntity:
    return OtpEntity(
        id=model.id,
        user_id=model.user_id,
        purpose=model.purpose,
        code_hash=model.code_hash,
        expires_at=model.expires_at,
        attempts=model.attempts,
        consumed_at=model.consumed_at,
        created_at=model.created_at,
    )


class SqlAlchemyOtpRepository(OtpRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, otp: OtpEntity) -> OtpEntity:
        model = OtpCode(
            id=otp.id,
            user_id=otp.user_id,
            purpose=otp.purpose,
            code_hash=otp.code_hash,
            expires_at=otp.expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_latest_usable(self, user_id: uuid.UUID, purpose: OtpPurpose) -> OtpEntity | None:
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(OtpCode)
            .where(OtpCode.user_id == user_id)
            .where(OtpCode.purpose == purpose)
            .where(OtpCode.consumed_at.is_(None))
            .where(OtpCode.expires_at > now)
            .where(OtpCode.attempts < 5)
            .order_by(OtpCode.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def increment_attempts(self, otp_id: uuid.UUID) -> None:
        await self._session.execute(
            update(OtpCode).where(OtpCode.id == otp_id).values(attempts=OtpCode.attempts + 1)
        )

    async def consume(self, otp_id: uuid.UUID) -> None:
        await self._session.execute(
            update(OtpCode).where(OtpCode.id == otp_id).values(consumed_at=datetime.now(UTC))
        )
