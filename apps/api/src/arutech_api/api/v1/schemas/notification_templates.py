import uuid
from datetime import datetime

from pydantic import BaseModel

from arutech_api.domain.notifications.entities import NotificationChannel


class NotificationTemplateResponse(BaseModel):
    id: uuid.UUID
    code: str
    channel: NotificationChannel
    subject: str | None
    body: str
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


class NotificationTemplateCreateRequest(BaseModel):
    code: str
    channel: NotificationChannel
    subject: str | None = None
    body: str


class NotificationTemplateUpdateRequest(BaseModel):
    subject: str | None = None
    body: str
