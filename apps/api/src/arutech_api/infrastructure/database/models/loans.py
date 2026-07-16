import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from arutech_api.domain.loans.entities import (
    CommissionStatus,
    EligibilityStatus,
    KycStatus,
    LoanApplicationStatus,
    LoanDocumentStatus,
    RiskCategory,
    VerificationStatus,
)
from arutech_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


def _enum(enum_cls: type, name: str) -> Enum:
    return Enum(
        enum_cls, name=name, values_callable=lambda cls: [member.value for member in cls]
    )


class LoanApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "loan_applications"

    customer_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True
    )
    loan_product_slug: Mapped[str] = mapped_column(String(100))
    requested_amount: Mapped[int] = mapped_column(Integer)
    tenure_months: Mapped[int] = mapped_column(Integer)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    monthly_income: Mapped[int] = mapped_column(Integer)
    existing_monthly_obligations: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[LoanApplicationStatus] = mapped_column(
        _enum(LoanApplicationStatus, "loan_application_status"),
        default=LoanApplicationStatus.DRAFT,
        index=True,
    )
    kyc_status: Mapped[KycStatus] = mapped_column(
        _enum(KycStatus, "kyc_status"), default=KycStatus.PENDING
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        _enum(VerificationStatus, "verification_status"), default=VerificationStatus.PENDING
    )
    eligibility_status: Mapped[EligibilityStatus] = mapped_column(
        _enum(EligibilityStatus, "eligibility_status"), default=EligibilityStatus.PENDING
    )
    credit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_category: Mapped[RiskCategory | None] = mapped_column(
        _enum(RiskCategory, "risk_category"), nullable=True
    )

    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    sanctioned_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sanctioned_tenure_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sanction_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    disbursed_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disbursement_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    disbursement_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    commission_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commission_status: Mapped[CommissionStatus | None] = mapped_column(
        _enum(CommissionStatus, "commission_status"), nullable=True
    )

    closure_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class LoanDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "loan_documents"

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), index=True
    )
    document_type: Mapped[str] = mapped_column(String(255))
    status: Mapped[LoanDocumentStatus] = mapped_column(
        _enum(LoanDocumentStatus, "loan_document_status"), default=LoanDocumentStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
