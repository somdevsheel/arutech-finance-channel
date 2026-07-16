import csv
import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from arutech_api.api.deps import get_lead_service, get_lead_task_service, require_permission
from arutech_api.api.v1.schemas.auth import AuditLogResponse
from arutech_api.api.v1.schemas.leads import (
    LeadAnalyticsResponse,
    LeadAssignRequest,
    LeadImportRequest,
    LeadResponse,
    LeadStatusUpdateRequest,
    LeadTaskCreateRequest,
    LeadTaskResponse,
)
from arutech_api.domain.leads.entities import LeadEntity, LeadStatus, LeadTaskEntity
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.lead_service import LeadImportItem, LeadService
from arutech_api.services.lead_task_service import LeadTaskService

router = APIRouter(prefix="/leads", tags=["leads"])

LeadServiceDep = Annotated[LeadService, Depends(get_lead_service)]
LeadTaskServiceDep = Annotated[LeadTaskService, Depends(get_lead_task_service)]
CanReadLeads = Annotated[UserEntity, Depends(require_permission("leads.read"))]
CanManageLeads = Annotated[UserEntity, Depends(require_permission("leads.manage"))]


def _lead_response(lead: LeadEntity) -> LeadResponse:
    return LeadResponse(
        id=lead.id,
        contact_submission_id=lead.contact_submission_id,
        source=lead.source,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        status=lead.status,
        score=lead.score,
        assigned_to=lead.assigned_to,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


def _task_response(task: LeadTaskEntity) -> LeadTaskResponse:
    return LeadTaskResponse(
        id=task.id,
        lead_id=task.lead_id,
        title=task.title,
        notes=task.notes,
        due_at=task.due_at,
        assigned_to=task.assigned_to,
        status=task.status,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


# --- Fixed-segment routes first: `/{lead_id}` below would otherwise treat
# a literal segment like "export" as a lead ID and 422 before this handler
# is ever reached. ---


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


@router.get("/export")
async def export_leads(
    _authorized: CanReadLeads,
    lead_service: LeadServiceDep,
    status: LeadStatus | None = None,
    assigned_to: uuid.UUID | None = None,
) -> StreamingResponse:
    leads = await lead_service.list_leads(
        status=status, assigned_to=assigned_to, limit=10_000, offset=0
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "name", "email", "phone", "source", "status", "score", "assigned_to", "created_at"]
    )
    for lead in leads:
        writer.writerow(
            [
                lead.id,
                lead.name,
                lead.email,
                lead.phone or "",
                lead.source.value,
                lead.status.value,
                lead.score,
                lead.assigned_to or "",
                lead.created_at.isoformat() if lead.created_at else "",
            ]
        )
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.post("/import", response_model=list[LeadResponse])
async def import_leads(
    payload: LeadImportRequest, _authorized: CanManageLeads, lead_service: LeadServiceDep
) -> list[LeadResponse]:
    items = [
        LeadImportItem(name=item.name, email=item.email, phone=item.phone)
        for item in payload.leads
    ]
    leads = await lead_service.import_leads(items)
    return [_lead_response(lead) for lead in leads]


@router.get("/analytics/summary", response_model=LeadAnalyticsResponse)
async def lead_analytics_summary(
    _authorized: CanReadLeads, lead_service: LeadServiceDep
) -> LeadAnalyticsResponse:
    summary = await lead_service.get_analytics_summary()
    return LeadAnalyticsResponse(
        total_leads=summary.total_leads,
        by_status=summary.by_status,
        by_source=summary.by_source,
        average_score=summary.average_score,
        conversion_rate=summary.conversion_rate,
    )


@router.get("/tasks/mine", response_model=list[LeadTaskResponse])
async def my_lead_tasks(
    authorized: CanReadLeads,
    task_service: LeadTaskServiceDep,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[LeadTaskResponse]:
    tasks = await task_service.list_for_assignee(authorized.id, limit=limit, offset=offset)
    return [_task_response(task) for task in tasks]


@router.post("/tasks/{task_id}/complete", response_model=LeadTaskResponse)
async def complete_lead_task(
    task_id: uuid.UUID, authorized: CanManageLeads, task_service: LeadTaskServiceDep
) -> LeadTaskResponse:
    task = await task_service.complete_task(task_id, actor_id=authorized.id)
    return _task_response(task)


# --- `/{lead_id}`-parametrized routes ---


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


@router.get("/{lead_id}/activity", response_model=list[AuditLogResponse])
async def lead_activity(
    lead_id: uuid.UUID, _authorized: CanReadLeads, lead_service: LeadServiceDep
) -> list[AuditLogResponse]:
    entries = await lead_service.get_activity(lead_id)
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


@router.get("/{lead_id}/tasks", response_model=list[LeadTaskResponse])
async def list_lead_tasks(
    lead_id: uuid.UUID, _authorized: CanReadLeads, task_service: LeadTaskServiceDep
) -> list[LeadTaskResponse]:
    tasks = await task_service.list_for_lead(lead_id)
    return [_task_response(task) for task in tasks]


@router.post("/{lead_id}/tasks", response_model=LeadTaskResponse)
async def create_lead_task(
    lead_id: uuid.UUID,
    payload: LeadTaskCreateRequest,
    authorized: CanManageLeads,
    task_service: LeadTaskServiceDep,
) -> LeadTaskResponse:
    task = await task_service.create_task(
        lead_id=lead_id,
        title=payload.title,
        due_at=payload.due_at,
        assigned_to=payload.assigned_to,
        notes=payload.notes,
        actor_id=authorized.id,
    )
    return _task_response(task)
