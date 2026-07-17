import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.loans.product_entities import LoanProductEntity
from arutech_api.domain.loans.product_repository import LoanProductRepository
from arutech_api.infrastructure.database.models.loan_products import LoanProduct


def _to_entity(model: LoanProduct) -> LoanProductEntity:
    return LoanProductEntity(
        id=model.id,
        slug=model.slug,
        name=model.name,
        interest_rate_min=model.interest_rate_min,
        interest_rate_max=model.interest_rate_max,
        tenure_min_months=model.tenure_min_months,
        tenure_max_months=model.tenure_max_months,
        amount_min=model.amount_min,
        amount_max=model.amount_max,
        documents_required=tuple(model.documents_required),
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyLoanProductRepository(LoanProductRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, product: LoanProductEntity) -> LoanProductEntity:
        model = LoanProduct(
            id=product.id,
            slug=product.slug,
            name=product.name,
            interest_rate_min=product.interest_rate_min,
            interest_rate_max=product.interest_rate_max,
            tenure_min_months=product.tenure_min_months,
            tenure_max_months=product.tenure_max_months,
            amount_min=product.amount_min,
            amount_max=product.amount_max,
            documents_required=list(product.documents_required),
            is_active=product.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, product_id: uuid.UUID) -> LoanProductEntity | None:
        model = await self._session.get(LoanProduct, product_id)
        return _to_entity(model) if model else None

    async def get_by_slug(self, slug: str) -> LoanProductEntity | None:
        result = await self._session.execute(select(LoanProduct).where(LoanProduct.slug == slug))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_products(self, *, is_active: bool | None = None) -> list[LoanProductEntity]:
        query = select(LoanProduct)
        if is_active is not None:
            query = query.where(LoanProduct.is_active.is_(is_active))
        result = await self._session.execute(query.order_by(LoanProduct.name))
        return [_to_entity(model) for model in result.scalars().all()]

    async def update(self, product: LoanProductEntity) -> LoanProductEntity:
        model = await self._session.get(LoanProduct, product.id)
        if model is None:
            raise NotFoundError(f"Loan product {product.id} not found")

        model.name = product.name
        model.interest_rate_min = product.interest_rate_min
        model.interest_rate_max = product.interest_rate_max
        model.tenure_min_months = product.tenure_min_months
        model.tenure_max_months = product.tenure_max_months
        model.amount_min = product.amount_min
        model.amount_max = product.amount_max
        model.documents_required = list(product.documents_required)
        model.is_active = product.is_active

        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def set_active(self, product_id: uuid.UUID, *, is_active: bool) -> LoanProductEntity:
        model = await self._session.get(LoanProduct, product_id)
        if model is None:
            raise NotFoundError(f"Loan product {product_id} not found")
        model.is_active = is_active
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
