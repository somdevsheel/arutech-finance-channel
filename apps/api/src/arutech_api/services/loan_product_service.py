import dataclasses
import uuid
from decimal import Decimal

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.loans.product_entities import LoanProductEntity
from arutech_api.domain.loans.product_repository import LoanProductRepository
from arutech_api.services.audit_service import AuditService

_ENTITY_TYPE = "loan_product"


class LoanProductService:
    """Phase 9's "Loan Product Management" / "Interest Rate Management" —
    admin CRUD over `LoanProductEntity`. `LoanApplicationService` (Phase
    7) is the other, much more frequent caller of
    `LoanProductRepository`, but only ever reads (`get_by_slug`); this
    service is the only writer."""

    def __init__(self, product_repo: LoanProductRepository, audit_service: AuditService):
        self._product_repo = product_repo
        self._audit_service = audit_service

    async def get_product(self, product_id: uuid.UUID) -> LoanProductEntity:
        product = await self._product_repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Loan product {product_id} not found")
        return product

    async def list_products(self, *, is_active: bool | None = None) -> list[LoanProductEntity]:
        return await self._product_repo.list_products(is_active=is_active)

    async def create_product(
        self,
        *,
        slug: str,
        name: str,
        interest_rate_min: Decimal,
        interest_rate_max: Decimal,
        tenure_min_months: int,
        tenure_max_months: int,
        amount_min: int,
        amount_max: int,
        documents_required: list[str],
        actor_id: uuid.UUID,
    ) -> LoanProductEntity:
        if await self._product_repo.get_by_slug(slug) is not None:
            raise ConflictError(f"A loan product with slug '{slug}' already exists")
        if interest_rate_min > interest_rate_max:
            raise ConflictError("interest_rate_min cannot exceed interest_rate_max")
        if tenure_min_months > tenure_max_months:
            raise ConflictError("tenure_min_months cannot exceed tenure_max_months")
        if amount_min > amount_max:
            raise ConflictError("amount_min cannot exceed amount_max")

        product = await self._product_repo.create(
            LoanProductEntity(
                slug=slug,
                name=name,
                interest_rate_min=interest_rate_min,
                interest_rate_max=interest_rate_max,
                tenure_min_months=tenure_min_months,
                tenure_max_months=tenure_max_months,
                amount_min=amount_min,
                amount_max=amount_max,
                documents_required=tuple(documents_required),
            )
        )
        await self._audit_service.record(
            action="loan_product.created",
            entity_type=_ENTITY_TYPE,
            entity_id=str(product.id),
            actor_id=actor_id,
        )
        return product

    async def update_product(
        self,
        product_id: uuid.UUID,
        *,
        name: str,
        interest_rate_min: Decimal,
        interest_rate_max: Decimal,
        tenure_min_months: int,
        tenure_max_months: int,
        amount_min: int,
        amount_max: int,
        documents_required: list[str],
        actor_id: uuid.UUID,
    ) -> LoanProductEntity:
        product = await self.get_product(product_id)
        if interest_rate_min > interest_rate_max:
            raise ConflictError("interest_rate_min cannot exceed interest_rate_max")
        if tenure_min_months > tenure_max_months:
            raise ConflictError("tenure_min_months cannot exceed tenure_max_months")
        if amount_min > amount_max:
            raise ConflictError("amount_min cannot exceed amount_max")

        updated = dataclasses.replace(
            product,
            name=name,
            interest_rate_min=interest_rate_min,
            interest_rate_max=interest_rate_max,
            tenure_min_months=tenure_min_months,
            tenure_max_months=tenure_max_months,
            amount_min=amount_min,
            amount_max=amount_max,
            documents_required=tuple(documents_required),
        )
        saved = await self._product_repo.update(updated)
        await self._audit_service.record(
            action="loan_product.updated",
            entity_type=_ENTITY_TYPE,
            entity_id=str(product_id),
            actor_id=actor_id,
        )
        return saved

    async def set_active(
        self, product_id: uuid.UUID, *, is_active: bool, actor_id: uuid.UUID
    ) -> LoanProductEntity:
        await self.get_product(product_id)  # 404s if unknown
        updated = await self._product_repo.set_active(product_id, is_active=is_active)
        await self._audit_service.record(
            action="loan_product.activated" if is_active else "loan_product.deactivated",
            entity_type=_ENTITY_TYPE,
            entity_id=str(product_id),
            actor_id=actor_id,
        )
        return updated
