import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from arutech_api.api.deps import get_lead_service, require_permission
from arutech_api.api.v1.schemas.leads import (
    LeadAssignRequest,
    LeadResponse,
    LeadStatusUpdateRequest,
)
from arutech_api.domain.leads.entities import LeadEntity, LeadStatus
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])

LeadServiceDep = Annotated[LeadService, Depends(get_lead_service)]
CanReadLeads = Annotated[UserEntity, Depends(require_permission("leads.read"))]
CanManageLeads = Annotated[UserEntity, Depends(require_permission("leads.manage"))]


def _lead_response(lead: LeadEntity) -> LeadResponse:
    return LeadResponse(
        id=lead.id,
        contact_submission_id=lead.contact_submission_id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        status=lead.status,
        score=lead.score,
        assigned_to=lead.assigned_to,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    _authorized: CanReadLeads,
    lead_service: LeadServiceDep,
    status: LeadStatus | None = None,
    assigned_to: uuid.UUID | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[LeadResponse]:
    leads = await lead_service.list_leads(
        status=status, assigned_to=assigned_to, limit=limit, offset=offset
    )
    return [_lead_response(lead) for lead in leads]


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: uuid.UUID, _authorized: CanReadLeads, lead_service: LeadServiceDep
) -> LeadResponse:
    lead = await lead_service.get_lead(lead_id)
    return _lead_response(lead)


@router.post("/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: uuid.UUID,
    payload: LeadStatusUpdateRequest,
    authorized: CanManageLeads,
    lead_service: LeadServiceDep,
) -> LeadResponse:
    lead = await lead_service.update_status(
        lead_id=lead_id, new_status=payload.status, actor_id=authorized.id
    )
    return _lead_response(lead)


@router.post("/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(
    lead_id: uuid.UUID,
    payload: LeadAssignRequest,
    authorized: CanManageLeads,
    lead_service: LeadServiceDep,
) -> LeadResponse:
    lead = await lead_service.assign(
        lead_id=lead_id, assignee_id=payload.assignee_id, actor_id=authorized.id
    )
    return _lead_response(lead)
