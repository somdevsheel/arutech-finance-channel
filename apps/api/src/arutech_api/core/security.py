"""Password hashing and JWT issuance/verification utilities.

Full login/OTP/refresh-rotation flows land in Phase 2 (Authentication).
This module only provides the reusable cryptographic primitives those
flows will be built on, so the RS256 keypair and hashing scheme don't
need to be revisited later.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from passlib.context import CryptContext

from arutech_api.core.config import settings

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired, or of the wrong type."""


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    return _pwd_context.needs_update(hashed_password)


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
    jti: str | None = None,
) -> tuple[str, str]:
    now = datetime.now(UTC)
    token_jti = jti or str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iss": settings.JWT_ISSUER,
        "iat": now,
        "exp": now + expires_delta,
        "jti": token_jti,
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, token_jti


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    token, _ = _create_token(
        subject,
        TokenType.ACCESS,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims,
    )
    return token


def create_refresh_token(subject: str) -> tuple[str, str]:
    """Returns `(token, jti)`. Unlike access tokens, refresh tokens are
    tracked server-side (see `infrastructure...refresh_token_repository`)
    so they can be listed as sessions and individually revoked — the caller
    needs the `jti` to persist alongside the token's hash."""
    return _create_token(
        subject,
        TokenType.REFRESH,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc

    if payload.get("type") != expected_type.value:
        raise TokenError(f"Expected a {expected_type.value} token")

    return payload


def _hmac_digest(value: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


def generate_otp_code() -> str:
    """A 6-digit numeric code. Uses `secrets` (CSPRNG), not `random`."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code: str) -> str:
    """HMAC-SHA256, not Argon2: OTPs are short-lived, rate-limited, 6-digit
    codes where verification speed matters more than memory-hardness — the
    slow-hashing properties that make Argon2 right for passwords aren't
    relevant here, and the real brute-force defense is the attempt cap and
    expiry enforced in the OTP repository, not the hash's cost."""
    return _hmac_digest(code)


def verify_otp(code: str, hashed_code: str) -> bool:
    return hmac.compare_digest(_hmac_digest(code), hashed_code)


def hash_refresh_token(token: str) -> str:
    """Refresh tokens are stored hashed (HMAC, same rationale as OTPs: this
    is a lookup/integrity check backed by expiry + revocation, not a
    password), so a leaked DB doesn't hand out usable tokens directly."""
    return _hmac_digest(token)
