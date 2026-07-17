import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from arutech_api.api.deps import get_rbac_service, require_permission
from arutech_api.api.v1.schemas.admin_rbac import (
    GrantPermissionRequest,
    PermissionResponse,
    RoleCreateRequest,
    RoleResponse,
)
from arutech_api.domain.rbac.entities import PermissionEntity, RoleEntity
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.rbac_service import RbacService

router = APIRouter(prefix="/admin", tags=["admin-rbac"])

RbacServiceDep = Annotated[RbacService, Depends(get_rbac_service)]
# roles.manage gates all of Role + Permission Management, read and write
# alike — see RbacService's docstring for why there's no separate
# read-only permission here.
CanManageRoles = Annotated[UserEntity, Depends(require_permission("roles.manage"))]


def _role_response(role: RoleEntity) -> RoleResponse:
    return RoleResponse(
        id=role.id, name=role.name, description=role.description, is_system=role.is_system
    )


def _permission_response(permission: PermissionEntity) -> PermissionResponse:
    return PermissionResponse(
        id=permission.id, code=permission.code, description=permission.description
    )


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(_authorized: CanManageRoles, service: RbacServiceDep) -> list[RoleResponse]:
    roles = await service.list_roles()
    return [_role_response(role) for role in roles]


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    payload: RoleCreateRequest, authorized: CanManageRoles, service: RbacServiceDep
) -> RoleResponse:
    role = await service.create_role(payload.name, payload.description, actor_id=authorized.id)
    return _role_response(role)


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: uuid.UUID, _authorized: CanManageRoles, service: RbacServiceDep
) -> RoleResponse:
    role = await service.get_role(role_id)
    return _role_response(role)


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: uuid.UUID, authorized: CanManageRoles, service: RbacServiceDep
) -> None:
    await service.delete_role(role_id, actor_id=authorized.id)


@router.get("/roles/{role_id}/permissions", response_model=list[PermissionResponse])
async def get_role_permissions(
    role_id: uuid.UUID, _authorized: CanManageRoles, service: RbacServiceDep
) -> list[PermissionResponse]:
    permissions = await service.get_role_permissions(role_id)
    return [_permission_response(permission) for permission in permissions]


@router.post("/roles/{role_id}/permissions", status_code=204)
async def grant_permission(
    role_id: uuid.UUID,
    payload: GrantPermissionRequest,
    authorized: CanManageRoles,
    service: RbacServiceDep,
) -> None:
    await service.grant_permission(role_id, payload.permission_code, actor_id=authorized.id)


@router.delete("/roles/{role_id}/permissions/{permission_code}", status_code=204)
async def revoke_permission(
    role_id: uuid.UUID,
    permission_code: str,
    authorized: CanManageRoles,
    service: RbacServiceDep,
) -> None:
    await service.revoke_permission(role_id, permission_code, actor_id=authorized.id)


@router.post("/roles/{role_id}/users/{user_id}", status_code=204)
async def assign_role_to_user(
    role_id: uuid.UUID, user_id: uuid.UUID, authorized: CanManageRoles, service: RbacServiceDep
) -> None:
    await service.assign_role_to_user(role_id, user_id, actor_id=authorized.id)


@router.delete("/roles/{role_id}/users/{user_id}", status_code=204)
async def remove_role_from_user(
    role_id: uuid.UUID, user_id: uuid.UUID, authorized: CanManageRoles, service: RbacServiceDep
) -> None:
    await service.remove_role_from_user(role_id, user_id, actor_id=authorized.id)


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    _authorized: CanManageRoles, service: RbacServiceDep
) -> list[PermissionResponse]:
    permissions = await service.list_permissions()
    return [_permission_response(permission) for permission in permissions]
