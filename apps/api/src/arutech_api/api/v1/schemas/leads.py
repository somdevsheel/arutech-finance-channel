import uuid
from datetime import datetime

from pydantic import BaseModel

from arutech_api.domain.leads.entities import LeadStatus

__all__ = ["LeadResponse", "LeadStatusUpdateRequest", "LeadAssignRequest"]


class LeadResponse(BaseModel):
    id: uuid.UUID
    contact_submission_id: uuid.UUID
    name: str
    email: str
    phone: str | None
    status: LeadStatus
    score: int
    assigned_to: uuid.UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class LeadStatusUpdateRequest(BaseModel):
    status: LeadStatus


class LeadAssignRequest(BaseModel):
    assignee_id: uuid.UUID
