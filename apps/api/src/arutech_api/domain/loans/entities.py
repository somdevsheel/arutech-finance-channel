import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class LoanApplicationStatus(StrEnum):
    """The main pipeline. KYC/verification/eligibility/credit are tracked
    as separate sub-statuses on the entity (see below) rather than more
    top-level states — they happen in parallel during UNDER_REVIEW, not
    in a fixed sequence, and APPROVED is only reachable once all three
    pass (see LoanApplicationService.approve)."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SANCTIONED = "sanctioned"
    DISBURSED = "disbursed"
    CLOSED = "closed"
    WITHDRAWN = "withdrawn"


TERMINAL_STATUSES = frozenset(
    {LoanApplicationStatus.REJECTED, LoanApplicationStatus.CLOSED, LoanApplicationStatus.WITHDRAWN}
)

ALLOWED_TRANSITIONS: dict[LoanApplicationStatus, frozenset[LoanApplicationStatus]] = {
    LoanApplicationStatus.DRAFT: frozenset(
        {LoanApplicationStatus.SUBMITTED, LoanApplicationStatus.WITHDRAWN}
    ),
    LoanApplicationStatus.SUBMITTED: frozenset(
        {LoanApplicationStatus.UNDER_REVIEW, LoanApplicationStatus.WITHDRAWN}
    ),
    LoanApplicationStatus.UNDER_REVIEW: frozenset(
        {LoanApplicationStatus.APPROVED, LoanApplicationStatus.REJECTED}
    ),
    LoanApplicationStatus.APPROVED: frozenset(
        {LoanApplicationStatus.SANCTIONED, LoanApplicationStatus.REJECTED}
    ),
    LoanApplicationStatus.REJECTED: frozenset(),
    LoanApplicationStatus.SANCTIONED: frozenset({LoanApplicationStatus.DISBURSED}),
    LoanApplicationStatus.DISBURSED: frozenset({LoanApplicationStatus.CLOSED}),
    LoanApplicationStatus.CLOSED: frozenset(),
    LoanApplicationStatus.WITHDRAWN: frozenset(),
}


def is_transition_allowed(current: LoanApplicationStatus, target: LoanApplicationStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


class KycStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class EligibilityStatus(StrEnum):
    PENDING = "pending"
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


class RiskCategory(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CommissionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"


class LoanDocumentStatus(StrEnum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class LoanApplicationEntity:
    """A loan application moving through origination. `lead_id` is
    provenance only (set when the applicant was a converted lead;
    Phase 5) — nothing here depends on it. Money fields are whole rupees
    (`int`); `interest_rate` is a percentage (`Decimal`, e.g. 10.5) to
    avoid the float-precision issues integer-rupee amounts don't have but
    a percentage rate does."""

    customer_user_id: uuid.UUID
    loan_product_slug: str
    requested_amount: int
    tenure_months: int
    interest_rate: Decimal
    monthly_income: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    lead_id: uuid.UUID | None = None
    existing_monthly_obligations: int = 0
    status: LoanApplicationStatus = LoanApplicationStatus.DRAFT
    kyc_status: KycStatus = KycStatus.PENDING
    verification_status: VerificationStatus = VerificationStatus.PENDING
    eligibility_status: EligibilityStatus = EligibilityStatus.PENDING
    credit_score: int | None = None
    risk_category: RiskCategory | None = None
    assigned_to: uuid.UUID | None = None
    rejection_reason: str | None = None
    sanctioned_amount: int | None = None
    sanctioned_tenure_months: int | None = None
    sanction_date: datetime | None = None
    disbursed_amount: int | None = None
    disbursement_date: datetime | None = None
    disbursement_reference: str | None = None
    commission_amount: int | None = None
    commission_status: CommissionStatus | None = None
    closure_date: datetime | None = None
    closure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LoanDocumentEntity:
    """A single checklist item. `document_type` is free text (e.g. "PAN
    card", "Last 6 months' bank statements") rather than a fixed enum —
    required documents vary widely by loan product (compare a gold loan's
    checklist to a home loan's in `apps/web/src/content/loan-
    products.ts`), and a rigid taxonomy would fit none of them well.
    Storage of the actual file is Phase 12's Document Management System;
    this tracks *that* a document was collected/verified, not the bytes."""

    application_id: uuid.UUID
    document_type: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: LoanDocumentStatus = LoanDocumentStatus.PENDING
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LoanAnalyticsSummary:
    total_applications: int
    by_status: dict[LoanApplicationStatus, int]
    by_product: dict[str, int]
    total_disbursed_amount: int
    total_commission_amount: int
