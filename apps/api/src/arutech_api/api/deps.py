import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.database import get_db
from arutech_api.core.exceptions import ForbiddenError, UnauthorizedError
from arutech_api.core.security import TokenError, TokenType, decode_token
from arutech_api.domain.audit.repository import AuditLogRepository
from arutech_api.domain.auth.ports import OtpDeliveryPort
from arutech_api.domain.auth.repository import OtpRepository, RefreshTokenRepository
from arutech_api.domain.contact.repository import ContactSubmissionRepository
from arutech_api.domain.rbac.repository import RbacRepository
from arutech_api.domain.users.entities import UserEntity
from arutech_api.domain.users.repository import UserRepository
from arutech_api.infrastructure.database.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from arutech_api.infrastructure.database.repositories.contact_repository import (
    SqlAlchemyContactSubmissionRepository,
)
from arutech_api.infrastructure.database.repositories.otp_repository import (
    SqlAlchemyOtpRepository,
)
from arutech_api.infrastructure.database.repositories.rbac_repository import (
    SqlAlchemyRbacRepository,
)
from arutech_api.infrastructure.database.repositories.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from arutech_api.infrastructure.database.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from arutech_api.infrastructure.notifications.log_otp_delivery import LoggingOtpDeliveryChannel
from arutech_api.services.audit_service import AuditService
from arutech_api.services.auth_service import AuthService
from arutech_api.services.contact_service import ContactService

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_user_repository(session: DbSession) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_refresh_token_repository(session: DbSession) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session)


def get_otp_repository(session: DbSession) -> OtpRepository:
    return SqlAlchemyOtpRepository(session)


def get_rbac_repository(session: DbSession) -> RbacRepository:
    return SqlAlchemyRbacRepository(session)


def get_audit_log_repository(session: DbSession) -> AuditLogRepository:
    return SqlAlchemyAuditLogRepository(session)


def get_contact_repository(session: DbSession) -> ContactSubmissionRepository:
    return SqlAlchemyContactSubmissionRepository(session)


def get_contact_service(
    contact_repo: Annotated[ContactSubmissionRepository, Depends(get_contact_repository)],
) -> ContactService:
    return ContactService(contact_repo)


_otp_delivery_channel = LoggingOtpDeliveryChannel()


def get_otp_delivery_channel() -> OtpDeliveryPort:
    return _otp_delivery_channel


def get_audit_service(
    audit_repo: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> AuditService:
    return AuditService(audit_repo)


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
    otp_repo: Annotated[OtpRepository, Depends(get_otp_repository)],
    rbac_repo: Annotated[RbacRepository, Depends(get_rbac_repository)],
    otp_delivery: Annotated[OtpDeliveryPort, Depends(get_otp_delivery_channel)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> AuthService:
    return AuthService(
        user_repo, refresh_token_repo, otp_repo, rbac_repo, otp_delivery, audit_service
    )


def get_client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserEntity:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")

    try:
        payload = decode_token(credentials.credentials, TokenType.ACCESS)
    except TokenError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc

    user = await user_repo.get_by_id(uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


CurrentUser = Annotated[UserEntity, Depends(get_current_user)]


def require_permission(
    code: str,
) -> Callable[..., Coroutine[Any, Any, UserEntity]]:
    """Dependency factory: `Depends(require_permission("audit_logs.read"))`.

    Re-fetches the user's permissions from the DB on every call rather than
    trusting a claim embedded in the access token, so a revoked permission
    takes effect on the next request instead of waiting out the token's
    lifetime (see docs/phase-2-architecture.md).
    """

    async def dependency(
        current_user: CurrentUser,
        rbac_repo: Annotated[RbacRepository, Depends(get_rbac_repository)],
    ) -> UserEntity:
        permissions = await rbac_repo.get_user_permission_codes(current_user.id)
        if code not in permissions:
            raise ForbiddenError(f"Missing required permission: {code}")
        return current_user

    return dependency
