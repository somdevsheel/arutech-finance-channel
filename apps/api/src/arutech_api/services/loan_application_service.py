import uuid
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.loans.calculations import assess_credit, assess_eligibility, calculate_emi
from arutech_api.domain.loans.document_repository import LoanDocumentRepository
from arutech_api.domain.loans.entities import (
    CommissionStatus,
    EligibilityStatus,
    KycStatus,
    LoanAnalyticsSummary,
    LoanApplicationEntity,
    LoanApplicationStatus,
    LoanDocumentEntity,
    VerificationStatus,
    is_transition_allowed,
)
from arutech_api.domain.loans.product_repository import LoanProductRepository
from arutech_api.domain.loans.repository import LoanApplicationRepository
from arutech_api.domain.users.entities import UserRole
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService

_ENTITY_TYPE = "loan_application"

# A flat, honest default — real per-partner commission rates are Phase
# 9/11's "Commission Management" territory. This exists so "Commission
# Tracking" produces a real number instead of nothing.
COMMISSION_RATE_PERCENT = Decimal("1")


class LoanApplicationService:
    def __init__(
        self,
        application_repo: LoanApplicationRepository,
        document_repo: LoanDocumentRepository,
        user_repo: UserRepository,
        product_repo: LoanProductRepository,
        audit_service: AuditService,
    ):
        self._application_repo = application_repo
        self._document_repo = document_repo
        self._user_repo = user_repo
        self._product_repo = product_repo
        self._audit_service = audit_service

    # --- creation & customer self-service -------------------------------

    async def create_draft(
        self,
        *,
        customer_user_id: uuid.UUID,
        loan_product_slug: str,
        requested_amount: int,
        tenure_months: int,
        monthly_income: int,
        existing_monthly_obligations: int = 0,
        interest_rate: Decimal | None = None,
        lead_id: uuid.UUID | None = None,
    ) -> LoanApplicationEntity:
        product = await self._product_repo.get_by_slug(loan_product_slug)
        if product is None:
            raise NotFoundError(f"Unknown loan product '{loan_product_slug}'")

        if not (product.amount_min <= requested_amount <= product.amount_max):
            raise ConflictError(
                f"Requested amount must be between {product.amount_min} and {product.amount_max}"
                f" for {product.name}"
            )
        if not (product.tenure_min_months <= tenure_months <= product.tenure_max_months):
            raise ConflictError(
                f"Tenure must be between {product.tenure_min_months} and "
                f"{product.tenure_max_months} months for {product.name}"
            )

        rate = interest_rate if interest_rate is not None else product.interest_rate_min
        if not (product.interest_rate_min <= rate <= product.interest_rate_max):
            raise ConflictError(
                f"Interest rate must be between {product.interest_rate_min}% and "
                f"{product.interest_rate_max}% for {product.name}"
            )

        application = await self._application_repo.create(
            LoanApplicationEntity(
                customer_user_id=customer_user_id,
                lead_id=lead_id,
                loan_product_slug=loan_product_slug,
                requested_amount=requested_amount,
                tenure_months=tenure_months,
                interest_rate=rate,
                monthly_income=monthly_income,
                existing_monthly_obligations=existing_monthly_obligations,
            )
        )
        await self._audit_service.record(
            action="loan_application.created",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application.id),
            actor_id=customer_user_id,
            metadata={"loan_product_slug": loan_product_slug},
        )
        return application

    async def get_own(
        self, application_id: uuid.UUID, customer_user_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self._application_repo.get_by_id(application_id)
        if application is None or application.customer_user_id != customer_user_id:
            # Same response for "doesn't exist" and "exists but isn't
            # yours" — a 403 here would confirm to a customer that some
            # other application ID is valid, just not theirs.
            raise NotFoundError("Loan application not found")
        return application

    async def list_own(self, customer_user_id: uuid.UUID) -> list[LoanApplicationEntity]:
        return await self._application_repo.list_applications(customer_user_id=customer_user_id)

    async def submit(
        self, application_id: uuid.UUID, customer_user_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_own(application_id, customer_user_id)
        self._transition_or_raise(application, LoanApplicationStatus.SUBMITTED)

        emi = calculate_emi(
            Decimal(application.requested_amount),
            application.interest_rate,
            application.tenure_months,
        )
        eligibility_status = assess_eligibility(
            monthly_income=Decimal(application.monthly_income),
            existing_monthly_obligations=Decimal(application.existing_monthly_obligations),
            emi=emi,
        )
        credit_score, risk_category = assess_credit(
            monthly_income=Decimal(application.monthly_income),
            emi=emi,
            tenure_months=application.tenure_months,
        )

        updated = replace(
            application,
            status=LoanApplicationStatus.SUBMITTED,
            eligibility_status=eligibility_status,
            credit_score=credit_score,
            risk_category=risk_category,
        )
        saved = await self._application_repo.update(updated)

        await self._seed_document_checklist(application)
        await self._audit_service.record(
            action="loan_application.submitted",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=customer_user_id,
            metadata={
                "eligibility_status": eligibility_status.value,
                "credit_score": credit_score,
                "risk_category": risk_category.value,
            },
        )
        return saved

    async def withdraw(
        self, application_id: uuid.UUID, customer_user_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_own(application_id, customer_user_id)
        self._transition_or_raise(application, LoanApplicationStatus.WITHDRAWN)

        saved = await self._application_repo.update(
            replace(application, status=LoanApplicationStatus.WITHDRAWN)
        )
        await self._audit_service.record(
            action="loan_application.withdrawn",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=customer_user_id,
        )
        return saved

    async def _seed_document_checklist(self, application: LoanApplicationEntity) -> None:
        product = await self._product_repo.get_by_slug(application.loan_product_slug)
        if product is None:
            return
        for document_type in product.documents_required:
            await self._document_repo.create(
                LoanDocumentEntity(
                    application_id=application.id, document_type=document_type
                )
            )

    # --- staff operations -------------------------------------------------

    def _transition_or_raise(
        self, application: LoanApplicationEntity, target: LoanApplicationStatus
    ) -> None:
        if not is_transition_allowed(application.status, target):
            raise ConflictError(
                f"Cannot move a loan application from '{application.status}' to '{target}'"
            )

    async def get_application(self, application_id: uuid.UUID) -> LoanApplicationEntity:
        application = await self._application_repo.get_by_id(application_id)
        if application is None:
            raise NotFoundError("Loan application not found")
        return application

    async def list_applications(
        self,
        *,
        status: LoanApplicationStatus | None = None,
        assigned_to: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LoanApplicationEntity]:
        return await self._application_repo.list_applications(
            status=status, assigned_to=assigned_to, limit=limit, offset=offset
        )

    async def assign(
        self, *, application_id: uuid.UUID, assignee_id: uuid.UUID, actor_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)

        assignee = await self._user_repo.get_by_id(assignee_id)
        if assignee is None:
            raise NotFoundError("Assignee not found")
        if assignee.role not in (UserRole.EMPLOYEE, UserRole.ADMIN):
            raise ConflictError("Loan applications can only be assigned to employees or admins")

        new_status = application.status
        if application.status == LoanApplicationStatus.SUBMITTED:
            new_status = LoanApplicationStatus.UNDER_REVIEW

        saved = await self._application_repo.update(
            replace(application, assigned_to=assignee_id, status=new_status)
        )
        await self._audit_service.record(
            action="loan_application.assigned",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
            metadata={"assigned_to": str(assignee_id)},
        )
        return saved

    async def update_kyc_status(
        self, *, application_id: uuid.UUID, status: KycStatus, actor_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)
        saved = await self._application_repo.update(replace(application, kyc_status=status))
        await self._audit_service.record(
            action="loan_application.kyc_updated",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
            metadata={"kyc_status": status.value},
        )
        return saved

    async def update_verification_status(
        self, *, application_id: uuid.UUID, status: VerificationStatus, actor_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)
        saved = await self._application_repo.update(
            replace(application, verification_status=status)
        )
        await self._audit_service.record(
            action="loan_application.verification_updated",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
            metadata={"verification_status": status.value},
        )
        return saved

    async def approve(
        self, *, application_id: uuid.UUID, actor_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)
        self._transition_or_raise(application, LoanApplicationStatus.APPROVED)

        if (
            application.kyc_status != KycStatus.VERIFIED
            or application.verification_status != VerificationStatus.VERIFIED
            or application.eligibility_status != EligibilityStatus.ELIGIBLE
        ):
            raise ConflictError(
                "Cannot approve until KYC and verification are VERIFIED and the "
                "applicant is ELIGIBLE"
            )

        saved = await self._application_repo.update(
            replace(application, status=LoanApplicationStatus.APPROVED)
        )
        await self._audit_service.record(
            action="loan_application.approved",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
        )
        return saved

    async def reject(
        self, *, application_id: uuid.UUID, reason: str, actor_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)
        self._transition_or_raise(application, LoanApplicationStatus.REJECTED)

        saved = await self._application_repo.update(
            replace(
                application, status=LoanApplicationStatus.REJECTED, rejection_reason=reason
            )
        )
        await self._audit_service.record(
            action="loan_application.rejected",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
            metadata={"reason": reason},
        )
        return saved

    async def sanction(
        self,
        *,
        application_id: uuid.UUID,
        sanctioned_amount: int,
        sanctioned_tenure_months: int,
        actor_id: uuid.UUID,
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)
        self._transition_or_raise(application, LoanApplicationStatus.SANCTIONED)

        if sanctioned_amount > application.requested_amount:
            raise ConflictError("Sanctioned amount cannot exceed the requested amount")

        saved = await self._application_repo.update(
            replace(
                application,
                status=LoanApplicationStatus.SANCTIONED,
                sanctioned_amount=sanctioned_amount,
                sanctioned_tenure_months=sanctioned_tenure_months,
                sanction_date=datetime.now(UTC),
            )
        )
        await self._audit_service.record(
            action="loan_application.sanctioned",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
            metadata={"sanctioned_amount": sanctioned_amount},
        )
        return saved

    async def disburse(
        self, *, application_id: uuid.UUID, disbursement_reference: str, actor_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)
        self._transition_or_raise(application, LoanApplicationStatus.DISBURSED)

        assert application.sanctioned_amount is not None  # guaranteed by the state machine
        commission_amount = int(
            Decimal(application.sanctioned_amount) * COMMISSION_RATE_PERCENT / Decimal(100)
        )

        saved = await self._application_repo.update(
            replace(
                application,
                status=LoanApplicationStatus.DISBURSED,
                disbursed_amount=application.sanctioned_amount,
                disbursement_date=datetime.now(UTC),
                disbursement_reference=disbursement_reference,
                commission_amount=commission_amount,
                commission_status=CommissionStatus.PENDING,
            )
        )
        await self._audit_service.record(
            action="loan_application.disbursed",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
            metadata={
                "disbursed_amount": application.sanctioned_amount,
                "commission_amount": commission_amount,
            },
        )
        return saved

    async def update_commission_status(
        self, *, application_id: uuid.UUID, status: CommissionStatus, actor_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)
        if application.commission_status is None:
            raise ConflictError("No commission has been computed for this application yet")

        saved = await self._application_repo.update(
            replace(application, commission_status=status)
        )
        await self._audit_service.record(
            action="loan_application.commission_updated",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
            metadata={"commission_status": status.value},
        )
        return saved

    async def close(
        self, *, application_id: uuid.UUID, closure_reason: str, actor_id: uuid.UUID
    ) -> LoanApplicationEntity:
        application = await self.get_application(application_id)
        self._transition_or_raise(application, LoanApplicationStatus.CLOSED)

        saved = await self._application_repo.update(
            replace(
                application,
                status=LoanApplicationStatus.CLOSED,
                closure_date=datetime.now(UTC),
                closure_reason=closure_reason,
            )
        )
        await self._audit_service.record(
            action="loan_application.closed",
            entity_type=_ENTITY_TYPE,
            entity_id=str(application_id),
            actor_id=actor_id,
            metadata={"closure_reason": closure_reason},
        )
        return saved

    async def get_analytics_summary(self) -> LoanAnalyticsSummary:
        return await self._application_repo.get_analytics_summary()
