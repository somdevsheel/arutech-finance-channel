import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from arutech_api.api.deps import get_user_admin_service, require_permission
from arutech_api.api.v1.schemas.admin_users import AdminUserResponse, SetRoleRequest
from arutech_api.domain.users.entities import UserEntity, UserRole
from arutech_api.services.user_admin_service import UserAdminService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

UserAdminServiceDep = Annotated[UserAdminService, Depends(get_user_admin_service)]
CanReadUsers = Annotated[UserEntity, Depends(require_permission("users.read"))]
CanManageUsers = Annotated[UserEntity, Depends(require_permission("users.manage"))]


def _to_response(user: UserEntity) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=list[AdminUserResponse])
async def list_users(
    _authorized: CanReadUsers,
    service: UserAdminServiceDep,
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(le=200)] = 50,
    offset: int = 0,
) -> list[AdminUserResponse]:
    users = await service.list_users(role=role, is_active=is_active, limit=limit, offset=offset)
    return [_to_response(user) for user in users]


@router.get("/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: uuid.UUID, _authorized: CanReadUsers, service: UserAdminServiceDep
) -> AdminUserResponse:
    user = await service.get_user(user_id)
    return _to_response(user)


@router.post("/{user_id}/activate", response_model=AdminUserResponse)
async def activate_user(
    user_id: uuid.UUID, authorized: CanManageUsers, service: UserAdminServiceDep
) -> AdminUserResponse:
    user = await service.set_active(user_id, is_active=True, actor_id=authorized.id)
    return _to_response(user)


@router.post("/{user_id}/deactivate", response_model=AdminUserResponse)
async def deactivate_user(
    user_id: uuid.UUID, authorized: CanManageUsers, service: UserAdminServiceDep
) -> AdminUserResponse:
    user = await service.set_active(user_id, is_active=False, actor_id=authorized.id)
    return _to_response(user)


@router.post("/{user_id}/role", response_model=AdminUserResponse)
async def set_user_role(
    user_id: uuid.UUID,
    payload: SetRoleRequest,
    authorized: CanManageUsers,
    service: UserAdminServiceDep,
) -> AdminUserResponse:
    user = await service.set_role(user_id, payload.role, actor_id=authorized.id)
    return _to_response(user)
