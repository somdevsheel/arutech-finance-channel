import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from arutech_api.domain.crm.entities import (
    CustomerSegment,
    InteractionChannel,
    InteractionDirection,
)

__all__ = [
    "CustomerUserSummary",
    "CustomerProfileResponse",
    "RelationshipManagerRequest",
    "SegmentUpdateRequest",
    "TagRequest",
    "InteractionCreateRequest",
    "InteractionResponse",
    "CustomerAnalyticsResponse",
    "CustomerTimelineEntryResponse",
]


class CustomerUserSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str | None


class CustomerProfileResponse(BaseModel):
    id: uuid.UUID
    user: CustomerUserSummary
    relationship_manager_id: uuid.UUID | None
    segment: CustomerSegment
    tags: list[str]
    created_at: datetime | None
    updated_at: datetime | None


class RelationshipManagerRequest(BaseModel):
    relationship_manager_id: uuid.UUID


class SegmentUpdateRequest(BaseModel):
    segment: CustomerSegment


class TagRequest(BaseModel):
    tag: str = Field(min_length=1, max_length=100)


class InteractionCreateRequest(BaseModel):
    channel: InteractionChannel
    summary: str = Field(min_length=1, max_length=500)
    notes: str | None = Field(default=None, max_length=5_000)
    direction: InteractionDirection = InteractionDirection.OUTBOUND
    occurred_at: datetime | None = None


class InteractionResponse(BaseModel):
    id: uuid.UUID
    customer_user_id: uuid.UUID
    channel: InteractionChannel
    direction: InteractionDirection
    summary: str
    notes: str | None
    occurred_at: datetime | None
    logged_by: uuid.UUID
    created_at: datetime | None


class CustomerAnalyticsResponse(BaseModel):
    total_customers: int
    by_segment: dict[CustomerSegment, int]
    customers_without_relationship_manager: int
    total_interactions: int
    by_channel: dict[InteractionChannel, int]


class CustomerTimelineEntryResponse(BaseModel):
    occurred_at: datetime
    kind: str
    summary: str
    detail: dict[str, Any] | None
