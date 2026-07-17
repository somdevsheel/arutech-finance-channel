import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from arutech_api.domain.lenders.entities import LenderType


class LenderResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: LenderType
    code: str
    contact_email: str | None
    contact_phone: str | None
    commission_rate_percent: Decimal
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


class LenderCreateRequest(BaseModel):
    name: str
    type: LenderType
    code: str
    contact_email: str | None = None
    contact_phone: str | None = None
    commission_rate_percent: Decimal = Decimal("1")


class LenderUpdateRequest(BaseModel):
    name: str
    contact_email: str | None = None
    contact_phone: str | None = None
    commission_rate_percent: Decimal
