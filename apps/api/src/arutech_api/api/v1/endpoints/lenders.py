import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from arutech_api.api.deps import get_lender_service, require_permission
from arutech_api.api.v1.schemas.lenders import (
    LenderCreateRequest,
    LenderResponse,
    LenderUpdateRequest,
)
from arutech_api.domain.lenders.entities import LenderEntity, LenderType
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.lender_service import LenderService

router = APIRouter(prefix="/lenders", tags=["lenders"])

LenderServiceDep = Annotated[LenderService, Depends(get_lender_service)]
CanReadLenders = Annotated[UserEntity, Depends(require_permission("lenders.read"))]
CanManageLenders = Annotated[UserEntity, Depends(require_permission("lenders.manage"))]


def _to_response(lender: LenderEntity) -> LenderResponse:
    return LenderResponse(
        id=lender.id,
        name=lender.name,
        type=lender.type,
        code=lender.code,
        contact_email=lender.contact_email,
        contact_phone=lender.contact_phone,
        commission_rate_percent=lender.commission_rate_percent,
        is_active=lender.is_active,
        created_at=lender.created_at,
        updated_at=lender.updated_at,
    )


@router.get("", response_model=list[LenderResponse])
async def list_lenders(
    _authorized: CanReadLenders,
    service: LenderServiceDep,
    type: LenderType | None = None,
    is_active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[LenderResponse]:
    lenders = await service.list_lenders(type=type, is_active=is_active, limit=limit, offset=offset)
    return [_to_response(lender) for lender in lenders]


@router.post("", response_model=LenderResponse)
async def create_lender(
    payload: LenderCreateRequest, authorized: CanManageLenders, service: LenderServiceDep
) -> LenderResponse:
    lender = await service.create_lender(
        name=payload.name,
        type=payload.type,
        code=payload.code,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        commission_rate_percent=payload.commission_rate_percent,
        actor_id=authorized.id,
    )
    return _to_response(lender)


@router.get("/{lender_id}", response_model=LenderResponse)
async def get_lender(
    lender_id: uuid.UUID, _authorized: CanReadLenders, service: LenderServiceDep
) -> LenderResponse:
    lender = await service.get_lender(lender_id)
    return _to_response(lender)


@router.put("/{lender_id}", response_model=LenderResponse)
async def update_lender(
    lender_id: uuid.UUID,
    payload: LenderUpdateRequest,
    authorized: CanManageLenders,
    service: LenderServiceDep,
) -> LenderResponse:
    lender = await service.update_lender(
        lender_id,
        name=payload.name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        commission_rate_percent=payload.commission_rate_percent,
        actor_id=authorized.id,
    )
    return _to_response(lender)


@router.post("/{lender_id}/activate", response_model=LenderResponse)
async def activate_lender(
    lender_id: uuid.UUID, authorized: CanManageLenders, service: LenderServiceDep
) -> LenderResponse:
    lender = await service.set_active(lender_id, is_active=True, actor_id=authorized.id)
    return _to_response(lender)


@router.post("/{lender_id}/deactivate", response_model=LenderResponse)
async def deactivate_lender(
    lender_id: uuid.UUID, authorized: CanManageLenders, service: LenderServiceDep
) -> LenderResponse:
    lender = await service.set_active(lender_id, is_active=False, actor_id=authorized.id)
    return _to_response(lender)
