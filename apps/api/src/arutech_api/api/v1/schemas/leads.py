import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from arutech_api.domain.leads.entities import LeadSource, LeadStatus, LeadTaskStatus

__all__ = [
    "LeadResponse",
    "LeadStatusUpdateRequest",
    "LeadAssignRequest",
    "LeadImportItemRequest",
    "LeadImportRequest",
    "LeadAnalyticsResponse",
    "LeadTaskCreateRequest",
    "LeadTaskResponse",
]


class LeadResponse(BaseModel):
    id: uuid.UUID
    contact_submission_id: uuid.UUID | None
    source: LeadSource
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


class LeadImportItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str
    phone: str | None = Field(default=None, max_length=20)


class LeadImportRequest(BaseModel):
    leads: list[LeadImportItemRequest] = Field(min_length=1, max_length=500)


class LeadAnalyticsResponse(BaseModel):
    total_leads: int
    by_status: dict[LeadStatus, int]
    by_source: dict[LeadSource, int]
    average_score: float
    conversion_rate: float


class LeadTaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    due_at: datetime
    assigned_to: uuid.UUID
    notes: str | None = Field(default=None, max_length=2_000)


class LeadTaskResponse(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    title: str
    notes: str | None
    due_at: datetime
    assigned_to: uuid.UUID
    status: LeadTaskStatus
    completed_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
