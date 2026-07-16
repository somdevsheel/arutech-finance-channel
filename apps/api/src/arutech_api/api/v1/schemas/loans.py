import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from arutech_api.domain.loans.entities import (
    CommissionStatus,
    EligibilityStatus,
    KycStatus,
    LoanApplicationStatus,
    LoanDocumentStatus,
    RiskCategory,
    VerificationStatus,
)

__all__ = [
    "LoanApplicationCreateRequest",
    "LoanApplicationResponse",
    "AssignRequest",
    "KycStatusUpdateRequest",
    "VerificationStatusUpdateRequest",
    "RejectRequest",
    "SanctionRequest",
    "DisburseRequest",
    "CommissionStatusUpdateRequest",
    "CloseRequest",
    "LoanDocumentResponse",
    "DocumentReviewRequest",
    "LoanAnalyticsResponse",
]


class LoanApplicationCreateRequest(BaseModel):
    loan_product_slug: str = Field(min_length=1, max_length=100)
    requested_amount: int = Field(gt=0)
    tenure_months: int = Field(gt=0)
    monthly_income: int = Field(gt=0)
    existing_monthly_obligations: int = Field(default=0, ge=0)
    interest_rate: Decimal | None = None
    lead_id: uuid.UUID | None = None


class LoanApplicationResponse(BaseModel):
    id: uuid.UUID
    customer_user_id: uuid.UUID
    lead_id: uuid.UUID | None
    loan_product_slug: str
    requested_amount: int
    tenure_months: int
    interest_rate: Decimal
    monthly_income: int
    existing_monthly_obligations: int
    status: LoanApplicationStatus
    kyc_status: KycStatus
    verification_status: VerificationStatus
    eligibility_status: EligibilityStatus
    credit_score: int | None
    risk_category: RiskCategory | None
    assigned_to: uuid.UUID | None
    rejection_reason: str | None
    sanctioned_amount: int | None
    sanctioned_tenure_months: int | None
    sanction_date: datetime | None
    disbursed_amount: int | None
    disbursement_date: datetime | None
    disbursement_reference: str | None
    commission_amount: int | None
    commission_status: CommissionStatus | None
    closure_date: datetime | None
    closure_reason: str | None
    created_at: datetime | None
    updated_at: datetime | None


class AssignRequest(BaseModel):
    assignee_id: uuid.UUID


class KycStatusUpdateRequest(BaseModel):
    status: KycStatus


class VerificationStatusUpdateRequest(BaseModel):
    status: VerificationStatus


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1_000)


class SanctionRequest(BaseModel):
    sanctioned_amount: int = Field(gt=0)
    sanctioned_tenure_months: int = Field(gt=0)


class DisburseRequest(BaseModel):
    disbursement_reference: str = Field(min_length=1, max_length=100)


class CommissionStatusUpdateRequest(BaseModel):
    status: CommissionStatus


class CloseRequest(BaseModel):
    closure_reason: str = Field(min_length=1, max_length=255)


class LoanDocumentResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    document_type: str
    status: LoanDocumentStatus
    notes: str | None
    created_at: datetime | None
    updated_at: datetime | None


class DocumentReviewRequest(BaseModel):
    status: LoanDocumentStatus
    notes: str | None = Field(default=None, max_length=1_000)


class LoanAnalyticsResponse(BaseModel):
    total_applications: int
    by_status: dict[LoanApplicationStatus, int]
    by_product: dict[str, int]
    total_disbursed_amount: int
    total_commission_amount: int
