import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.auth.entities import OtpEntity, OtpPurpose, RefreshTokenEntity


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def create(self, token: RefreshTokenEntity) -> RefreshTokenEntity: ...

    @abstractmethod
    async def get_by_jti(self, jti: str) -> RefreshTokenEntity | None: ...

    @abstractmethod
    async def list_active_for_user(self, user_id: uuid.UUID) -> list[RefreshTokenEntity]: ...

    @abstractmethod
    async def revoke(self, token_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None: ...


class OtpRepository(ABC):
    @abstractmethod
    async def create(self, otp: OtpEntity) -> OtpEntity: ...

    @abstractmethod
    async def get_latest_usable(
        self, user_id: uuid.UUID, purpose: OtpPurpose
    ) -> OtpEntity | None: ...

    @abstractmethod
    async def increment_attempts(self, otp_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def consume(self, otp_id: uuid.UUID) -> None: ...
