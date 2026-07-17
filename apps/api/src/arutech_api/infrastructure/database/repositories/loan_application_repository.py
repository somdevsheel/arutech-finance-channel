import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.loans.entities import (
    LoanAnalyticsSummary,
    LoanApplicationEntity,
    LoanApplicationStatus,
)
from arutech_api.domain.loans.repository import LoanApplicationRepository
from arutech_api.infrastructure.database.models.loans import LoanApplication


def _to_entity(model: LoanApplication) -> LoanApplicationEntity:
    return LoanApplicationEntity(
        id=model.id,
        customer_user_id=model.customer_user_id,
        lead_id=model.lead_id,
        loan_product_slug=model.loan_product_slug,
        requested_amount=model.requested_amount,
        tenure_months=model.tenure_months,
        interest_rate=model.interest_rate,
        monthly_income=model.monthly_income,
        existing_monthly_obligations=model.existing_monthly_obligations,
        status=model.status,
        kyc_status=model.kyc_status,
        verification_status=model.verification_status,
        eligibility_status=model.eligibility_status,
        credit_score=model.credit_score,
        risk_category=model.risk_category,
        assigned_to=model.assigned_to,
        rejection_reason=model.rejection_reason,
        sanctioned_amount=model.sanctioned_amount,
        sanctioned_tenure_months=model.sanctioned_tenure_months,
        sanction_date=model.sanction_date,
        disbursed_amount=model.disbursed_amount,
        disbursement_date=model.disbursement_date,
        disbursement_reference=model.disbursement_reference,
        commission_amount=model.commission_amount,
        commission_status=model.commission_status,
        closure_date=model.closure_date,
        closure_reason=model.closure_reason,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _apply_entity(model: LoanApplication, entity: LoanApplicationEntity) -> None:
    model.customer_user_id = entity.customer_user_id
    model.lead_id = entity.lead_id
    model.loan_product_slug = entity.loan_product_slug
    model.requested_amount = entity.requested_amount
    model.tenure_months = entity.tenure_months
    model.interest_rate = entity.interest_rate
    model.monthly_income = entity.monthly_income
    model.existing_monthly_obligations = entity.existing_monthly_obligations
    model.status = entity.status
    model.kyc_status = entity.kyc_status
    model.verification_status = entity.verification_status
    model.eligibility_status = entity.eligibility_status
    model.credit_score = entity.credit_score
    model.risk_category = entity.risk_category
    model.assigned_to = entity.assigned_to
    model.rejection_reason = entity.rejection_reason
    model.sanctioned_amount = entity.sanctioned_amount
    model.sanctioned_tenure_months = entity.sanctioned_tenure_months
    model.sanction_date = entity.sanction_date
    model.disbursed_amount = entity.disbursed_amount
    model.disbursement_date = entity.disbursement_date
    model.disbursement_reference = entity.disbursement_reference
    model.commission_amount = entity.commission_amount
    model.commission_status = entity.commission_status
    model.closure_date = entity.closure_date
    model.closure_reason = entity.closure_reason


class SqlAlchemyLoanApplicationRepository(LoanApplicationRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, application: LoanApplicationEntity) -> LoanApplicationEntity:
        model = LoanApplication(id=application.id)
        _apply_entity(model, application)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, application_id: uuid.UUID) -> LoanApplicationEntity | None:
        result = await self._session.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_applications(
        self,
        *,
        status: LoanApplicationStatus | None = None,
        assigned_to: uuid.UUID | None = None,
        customer_user_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LoanApplicationEntity]:
        query = select(LoanApplication)
        if status is not None:
            query = query.where(LoanApplication.status == status)
        if assigned_to is not None:
            query = query.where(LoanApplication.assigned_to == assigned_to)
        if customer_user_id is not None:
            query = query.where(LoanApplication.customer_user_id == customer_user_id)
        query = query.order_by(LoanApplication.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def update(self, application: LoanApplicationEntity) -> LoanApplicationEntity:
        result = await self._session.execute(
            select(LoanApplication).where(LoanApplication.id == application.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError("Loan application not found")

        _apply_entity(model, application)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_analytics_summary(self) -> LoanAnalyticsSummary:
        total = (await self._session.execute(select(func.count(LoanApplication.id)))).scalar_one()

        by_status_rows = (
            await self._session.execute(
                select(LoanApplication.status, func.count(LoanApplication.id)).group_by(
                    LoanApplication.status
                )
            )
        ).all()
        by_status: dict[LoanApplicationStatus, int] = {
            status: count for status, count in by_status_rows
        }

        by_product_rows = (
            await self._session.execute(
                select(LoanApplication.loan_product_slug, func.count(LoanApplication.id)).group_by(
                    LoanApplication.loan_product_slug
                )
            )
        ).all()
        by_product: dict[str, int] = {product: count for product, count in by_product_rows}

        total_disbursed = (
            await self._session.execute(select(func.sum(LoanApplication.disbursed_amount)))
        ).scalar_one()
        total_commission = (
            await self._session.execute(select(func.sum(LoanApplication.commission_amount)))
        ).scalar_one()

        return LoanAnalyticsSummary(
            total_applications=total,
            by_status=by_status,
            by_product=by_product,
            total_disbursed_amount=total_disbursed or 0,
            total_commission_amount=total_commission or 0,
        )

    async def get_hourly_activity_counts(self) -> dict[tuple[int, int], int]:
        # See LeadRepository.get_hourly_activity_counts for why DOW, not
        # ISODOW: SQLite's extract_map (used by the test suite) has no
        # ISODOW equivalent.
        day_of_week = func.extract("dow", LoanApplication.created_at)
        hour = func.extract("hour", LoanApplication.created_at)
        query = select(day_of_week, hour, func.count(LoanApplication.id)).group_by(
            day_of_week, hour
        )
        rows = (await self._session.execute(query)).all()
        return {(int(day), int(hour)): count for day, hour, count in rows}
