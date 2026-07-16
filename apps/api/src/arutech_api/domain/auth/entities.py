import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class OtpPurpose(StrEnum):
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"


@dataclass(frozen=True, slots=True)
class RefreshTokenEntity:
    """A revocable, listable session. One row per issued refresh token."""

    id: uuid.UUID
    user_id: uuid.UUID
    jti: str
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
    user_agent: str | None = None
    ip_address: str | None = None
    created_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.now(self.expires_at.tzinfo)


@dataclass(frozen=True, slots=True)
class OtpEntity:
    id: uuid.UUID
    user_id: uuid.UUID
    purpose: OtpPurpose
    code_hash: str
    expires_at: datetime
    attempts: int = 0
    consumed_at: datetime | None = None
    created_at: datetime | None = None

    @property
    def is_usable(self) -> bool:
        now = datetime.now(self.expires_at.tzinfo)
        return self.consumed_at is None and self.expires_at > now and self.attempts < 5
