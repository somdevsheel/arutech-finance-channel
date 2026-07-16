import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi import status as http_status

from arutech_api.api.deps import (
    CurrentUser,
    get_audit_service,
    get_auth_service,
    get_client_ip,
    get_user_agent,
    require_permission,
)
from arutech_api.api.v1.schemas.auth import (
    AuditLogResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    OtpRequestRequest,
    OtpVerifyRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequestRequest,
    RefreshRequest,
    RegisterRequest,
    SessionResponse,
    TokenResponse,
    UserResponse,
)
from arutech_api.core.rate_limit import limiter
from arutech_api.domain.auth.entities import RefreshTokenEntity
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.audit_service import AuditService
from arutech_api.services.auth_service import AuthResult, AuthService, RequestContext

router = APIRouter(prefix="/auth", tags=["auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]


def _context(request: Request) -> RequestContext:
    return RequestContext(ip_address=get_client_ip(request), user_agent=get_user_agent(request))


def _user_response(user: UserEntity) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


def _token_response(result: AuthResult) -> TokenResponse:
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        user=_user_response(result.user),
    )


def _session_response(session: RefreshTokenEntity) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        user_agent=session.user_agent,
        ip_address=session.ip_address,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


@router.post("/register", response_model=UserResponse, status_code=http_status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request, payload: RegisterRequest, auth_service: AuthServiceDep
) -> UserResponse:
    user = await auth_service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        phone=payload.phone,
        context=_context(request),
    )
    return _user_response(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request, payload: LoginRequest, auth_service: AuthServiceDep
) -> TokenResponse:
    result = await auth_service.login(
        email=payload.email, password=payload.password, context=_context(request)
    )
    return _token_response(result)


@router.post("/otp/request", response_model=MessageResponse)
@limiter.limit("3/minute")
async def request_otp(
    request: Request, payload: OtpRequestRequest, auth_service: AuthServiceDep
) -> MessageResponse:
    await auth_service.request_login_otp(email=payload.email, context=_context(request))
    return MessageResponse(message="If that account exists, a verification code has been sent.")


@router.post("/otp/verify", response_model=TokenResponse)
@limiter.limit("10/minute")
async def verify_otp(
    request: Request, payload: OtpVerifyRequest, auth_service: AuthServiceDep
) -> TokenResponse:
    result = await auth_service.verify_login_otp(
        email=payload.email, code=payload.code, context=_context(request)
    )
    return _token_response(result)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh(
    request: Request, payload: RefreshRequest, auth_service: AuthServiceDep
) -> TokenResponse:
    result = await auth_service.refresh(
        refresh_token=payload.refresh_token, context=_context(request)
    )
    return _token_response(result)


@router.post("/logout", response_model=MessageResponse)
async def logout(payload: LogoutRequest, auth_service: AuthServiceDep) -> MessageResponse:
    await auth_service.logout(refresh_token=payload.refresh_token)
    return MessageResponse(message="Logged out")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(current_user: CurrentUser, auth_service: AuthServiceDep) -> MessageResponse:
    await auth_service.logout_all(user_id=current_user.id)
    return MessageResponse(message="Logged out of all sessions")


@router.post("/password-reset/request", response_model=MessageResponse)
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request, payload: PasswordResetRequestRequest, auth_service: AuthServiceDep
) -> MessageResponse:
    await auth_service.request_password_reset(email=payload.email, context=_context(request))
    return MessageResponse(message="If that account exists, a reset code has been sent.")


@router.post("/password-reset/confirm", response_model=MessageResponse)
@limiter.limit("5/minute")
async def confirm_password_reset(
    request: Request, payload: PasswordResetConfirmRequest, auth_service: AuthServiceDep
) -> MessageResponse:
    await auth_service.confirm_password_reset(
        email=payload.email,
        code=payload.code,
        new_password=payload.new_password,
        context=_context(request),
    )
    return MessageResponse(message="Password has been reset")


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return _user_response(current_user)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: CurrentUser, auth_service: AuthServiceDep
) -> list[SessionResponse]:
    sessions = await auth_service.list_sessions(user_id=current_user.id)
    return [_session_response(s) for s in sessions]


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: uuid.UUID, current_user: CurrentUser, auth_service: AuthServiceDep
) -> MessageResponse:
    await auth_service.revoke_session(user_id=current_user.id, session_id=session_id)
    return MessageResponse(message="Session revoked")


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    _authorized: Annotated[UserEntity, Depends(require_permission("audit_logs.read"))],
    audit_service: AuditServiceDep,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLogResponse]:
    entries = await audit_service.list_recent(limit=limit, offset=offset)
    return [
        AuditLogResponse(
            id=e.id,
            actor_id=e.actor_id,
            action=e.action,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            extra_metadata=e.extra_metadata,
            created_at=e.created_at,
        )
        for e in entries
    ]
