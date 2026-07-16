import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from arutech_api.core.config import settings
from arutech_api.core.exceptions import ConflictError, UnauthorizedError
from arutech_api.core.security import (
    TokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp_code,
    hash_otp,
    hash_password,
    hash_refresh_token,
    verify_otp,
    verify_password,
)
from arutech_api.domain.auth.entities import OtpEntity, OtpPurpose, RefreshTokenEntity
from arutech_api.domain.auth.ports import OtpDeliveryPort
from arutech_api.domain.auth.repository import OtpRepository, RefreshTokenRepository
from arutech_api.domain.rbac.repository import RbacRepository
from arutech_api.domain.users.entities import UserEntity, UserRole
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService

_GENERIC_LOGIN_ERROR = "Invalid credentials"
_GENERIC_OTP_ERROR = "Invalid or expired code"


@dataclass(frozen=True, slots=True)
class AuthResult:
    access_token: str
    refresh_token: str
    user: UserEntity


@dataclass(frozen=True, slots=True)
class RequestContext:
    ip_address: str | None = None
    user_agent: str | None = None


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        otp_repo: OtpRepository,
        rbac_repo: RbacRepository,
        otp_delivery: OtpDeliveryPort,
        audit_service: AuditService,
    ):
        self._users = user_repo
        self._refresh_tokens = refresh_token_repo
        self._otps = otp_repo
        self._rbac = rbac_repo
        self._otp_delivery = otp_delivery
        self._audit = audit_service

    # --- Registration -----------------------------------------------------

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        phone: str | None,
        context: RequestContext,
    ) -> UserEntity:
        if await self._users.exists_by_email(email):
            raise ConflictError("An account with this email already exists")

        # Public self-registration only ever creates customer accounts;
        # employee/partner/admin accounts are provisioned by admins
        # (Phase 9/10/11), never via this endpoint.
        user = await self._users.create(
            UserEntity(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                phone=phone,
                role=UserRole.CUSTOMER,
            )
        )

        role = await self._rbac.get_role_by_name(UserRole.CUSTOMER.value)
        if role is not None:
            await self._rbac.assign_role_to_user(user.id, role.id)

        await self._audit.record(
            action="user.registered",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            metadata={"email": email, "ip_address": context.ip_address},
        )
        return user

    # --- Password login -----------------------------------------------------

    async def login(self, *, email: str, password: str, context: RequestContext) -> AuthResult:
        user = await self._users.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            await self._audit.record(
                action="user.login_failed",
                entity_type="user",
                entity_id=str(user.id) if user else email,
                actor_id=user.id if user else None,
                metadata={
                    "email": email,
                    "ip_address": context.ip_address,
                    "reason": "bad_credentials",
                },
            )
            raise UnauthorizedError(_GENERIC_LOGIN_ERROR)

        if not user.is_active:
            await self._audit.record(
                action="user.login_failed",
                entity_type="user",
                entity_id=str(user.id),
                actor_id=user.id,
                metadata={"email": email, "ip_address": context.ip_address, "reason": "inactive"},
            )
            raise UnauthorizedError(_GENERIC_LOGIN_ERROR)

        result = await self._issue_tokens(user, context)
        await self._audit.record(
            action="user.login",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            metadata={"ip_address": context.ip_address, "method": "password"},
        )
        return result

    # --- OTP login -----------------------------------------------------

    async def request_login_otp(self, *, email: str, context: RequestContext) -> None:
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            # Deliberately silent: the caller always sees the same generic
            # "if that account exists, a code was sent" response, so this
            # can't be used to enumerate registered emails.
            return

        await self._create_and_send_otp(user, OtpPurpose.LOGIN)
        await self._audit.record(
            action="otp.requested",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            metadata={"purpose": OtpPurpose.LOGIN.value, "ip_address": context.ip_address},
        )

    async def verify_login_otp(
        self, *, email: str, code: str, context: RequestContext
    ) -> AuthResult:
        user = await self._users.get_by_email(email)
        if user is None:
            raise UnauthorizedError(_GENERIC_OTP_ERROR)

        await self._consume_otp(user, code, OtpPurpose.LOGIN)

        result = await self._issue_tokens(user, context)
        await self._audit.record(
            action="user.login",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            metadata={"ip_address": context.ip_address, "method": "otp"},
        )
        return result

    # --- Password reset -----------------------------------------------------

    async def request_password_reset(self, *, email: str, context: RequestContext) -> None:
        user = await self._users.get_by_email(email)
        if user is None:
            return  # Same enumeration-avoidance rationale as request_login_otp.

        await self._create_and_send_otp(user, OtpPurpose.PASSWORD_RESET)
        await self._audit.record(
            action="password_reset.requested",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            metadata={"ip_address": context.ip_address},
        )

    async def confirm_password_reset(
        self, *, email: str, code: str, new_password: str, context: RequestContext
    ) -> None:
        user = await self._users.get_by_email(email)
        if user is None:
            raise UnauthorizedError(_GENERIC_OTP_ERROR)

        await self._consume_otp(user, code, OtpPurpose.PASSWORD_RESET)

        updated = UserEntity(
            id=user.id,
            email=user.email,
            hashed_password=hash_password(new_password),
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )
        await self._users.update(updated)

        # A password reset invalidates every existing session — the whole
        # point is that anyone who had access via the old password shouldn't
        # still have a live session afterwards.
        await self._refresh_tokens.revoke_all_for_user(user.id)

        await self._audit.record(
            action="password.reset",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            metadata={"ip_address": context.ip_address},
        )

    # --- Refresh / logout / sessions -----------------------------------------------------

    async def refresh(self, *, refresh_token: str, context: RequestContext) -> AuthResult:
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH)
        except TokenError as exc:
            raise UnauthorizedError("Invalid or expired refresh token") from exc

        stored = await self._refresh_tokens.get_by_jti(payload["jti"])
        if stored is None or stored.token_hash != hash_refresh_token(refresh_token):
            raise UnauthorizedError("Invalid or expired refresh token")

        if stored.revoked_at is not None:
            # This token was already rotated away once; seeing it again
            # means it leaked. Burn every session for this user, not just
            # this one, per standard refresh-token-rotation practice.
            await self._refresh_tokens.revoke_all_for_user(stored.user_id)
            await self._audit.record(
                action="refresh_token.reuse_detected",
                entity_type="user",
                entity_id=str(stored.user_id),
                actor_id=stored.user_id,
                metadata={"ip_address": context.ip_address},
            )
            raise UnauthorizedError("Invalid or expired refresh token")

        if not stored.is_active:
            raise UnauthorizedError("Invalid or expired refresh token")

        user = await self._users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid or expired refresh token")

        await self._refresh_tokens.revoke(stored.id)
        result = await self._issue_tokens(user, context)
        await self._audit.record(
            action="token.refreshed",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            metadata={"ip_address": context.ip_address},
        )
        return result

    async def logout(self, *, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH)
        except TokenError:
            return  # Logout is idempotent: an already-invalid token is a no-op.

        stored = await self._refresh_tokens.get_by_jti(payload["jti"])
        if stored is not None and stored.revoked_at is None:
            await self._refresh_tokens.revoke(stored.id)
            await self._audit.record(
                action="user.logout",
                entity_type="user",
                entity_id=str(stored.user_id),
                actor_id=stored.user_id,
            )

    async def logout_all(self, *, user_id: uuid.UUID) -> None:
        await self._refresh_tokens.revoke_all_for_user(user_id)
        await self._audit.record(
            action="user.logout_all", entity_type="user", entity_id=str(user_id), actor_id=user_id
        )

    async def list_sessions(self, *, user_id: uuid.UUID) -> list[RefreshTokenEntity]:
        return await self._refresh_tokens.list_active_for_user(user_id)

    async def revoke_session(self, *, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
        sessions = await self._refresh_tokens.list_active_for_user(user_id)
        if not any(s.id == session_id for s in sessions):
            raise UnauthorizedError("Session not found")
        await self._refresh_tokens.revoke(session_id)
        await self._audit.record(
            action="session.revoked",
            entity_type="refresh_token",
            entity_id=str(session_id),
            actor_id=user_id,
        )

    # --- Internals -----------------------------------------------------

    async def _issue_tokens(self, user: UserEntity, context: RequestContext) -> AuthResult:
        access_token = create_access_token(str(user.id), extra_claims={"role": user.role.value})
        refresh_token, jti = create_refresh_token(str(user.id))

        await self._refresh_tokens.create(
            RefreshTokenEntity(
                id=uuid.uuid4(),
                user_id=user.id,
                jti=jti,
                token_hash=hash_refresh_token(refresh_token),
                expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                user_agent=context.user_agent,
                ip_address=context.ip_address,
            )
        )
        return AuthResult(access_token=access_token, refresh_token=refresh_token, user=user)

    async def _create_and_send_otp(self, user: UserEntity, purpose: OtpPurpose) -> None:
        code = generate_otp_code()
        await self._otps.create(
            OtpEntity(
                id=uuid.uuid4(),
                user_id=user.id,
                purpose=purpose,
                code_hash=hash_otp(code),
                expires_at=datetime.now(UTC) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            )
        )
        destination = user.phone or user.email
        await self._otp_delivery.send(destination, code, purpose)

    async def _consume_otp(self, user: UserEntity, code: str, purpose: OtpPurpose) -> None:
        otp = await self._otps.get_latest_usable(user.id, purpose)
        if otp is None:
            raise UnauthorizedError(_GENERIC_OTP_ERROR)

        if not verify_otp(code, otp.code_hash):
            await self._otps.increment_attempts(otp.id)
            raise UnauthorizedError(_GENERIC_OTP_ERROR)

        await self._otps.consume(otp.id)
