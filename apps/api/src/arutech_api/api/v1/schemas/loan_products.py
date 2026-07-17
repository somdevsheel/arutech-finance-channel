import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class LoanProductResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    interest_rate_min: Decimal
    interest_rate_max: Decimal
    tenure_min_months: int
    tenure_max_months: int
    amount_min: int
    amount_max: int
    documents_required: list[str]
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


class LoanProductCreateRequest(BaseModel):
    slug: str
    name: str
    interest_rate_min: Decimal
    interest_rate_max: Decimal
    tenure_min_months: int
    tenure_max_months: int
    amount_min: int
    amount_max: int
    documents_required: list[str] = []


class LoanProductUpdateRequest(BaseModel):
    name: str
    interest_rate_min: Decimal
    interest_rate_max: Decimal
    tenure_min_months: int
    tenure_max_months: int
    amount_min: int
    amount_max: int
    documents_required: list[str] = []
