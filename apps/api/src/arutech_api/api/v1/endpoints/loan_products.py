import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from arutech_api.api.deps import get_loan_product_service, require_permission
from arutech_api.api.v1.schemas.loan_products import (
    LoanProductCreateRequest,
    LoanProductResponse,
    LoanProductUpdateRequest,
)
from arutech_api.domain.loans.product_entities import LoanProductEntity
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.loan_product_service import LoanProductService

router = APIRouter(prefix="/loan-products", tags=["loan-products"])

LoanProductServiceDep = Annotated[LoanProductService, Depends(get_loan_product_service)]
CanReadLoanProducts = Annotated[UserEntity, Depends(require_permission("loan_products.read"))]
CanManageLoanProducts = Annotated[UserEntity, Depends(require_permission("loan_products.manage"))]


def _to_response(product: LoanProductEntity) -> LoanProductResponse:
    return LoanProductResponse(
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
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get("", response_model=list[LoanProductResponse])
async def list_loan_products(
    _authorized: CanReadLoanProducts,
    service: LoanProductServiceDep,
    is_active: bool | None = None,
) -> list[LoanProductResponse]:
    products = await service.list_products(is_active=is_active)
    return [_to_response(product) for product in products]


@router.post("", response_model=LoanProductResponse)
async def create_loan_product(
    payload: LoanProductCreateRequest,
    authorized: CanManageLoanProducts,
    service: LoanProductServiceDep,
) -> LoanProductResponse:
    product = await service.create_product(
        slug=payload.slug,
        name=payload.name,
        interest_rate_min=payload.interest_rate_min,
        interest_rate_max=payload.interest_rate_max,
        tenure_min_months=payload.tenure_min_months,
        tenure_max_months=payload.tenure_max_months,
        amount_min=payload.amount_min,
        amount_max=payload.amount_max,
        documents_required=payload.documents_required,
        actor_id=authorized.id,
    )
    return _to_response(product)


@router.get("/{product_id}", response_model=LoanProductResponse)
async def get_loan_product(
    product_id: uuid.UUID, _authorized: CanReadLoanProducts, service: LoanProductServiceDep
) -> LoanProductResponse:
    product = await service.get_product(product_id)
    return _to_response(product)


@router.put("/{product_id}", response_model=LoanProductResponse)
async def update_loan_product(
    product_id: uuid.UUID,
    payload: LoanProductUpdateRequest,
    authorized: CanManageLoanProducts,
    service: LoanProductServiceDep,
) -> LoanProductResponse:
    product = await service.update_product(
        product_id,
        name=payload.name,
        interest_rate_min=payload.interest_rate_min,
        interest_rate_max=payload.interest_rate_max,
        tenure_min_months=payload.tenure_min_months,
        tenure_max_months=payload.tenure_max_months,
        amount_min=payload.amount_min,
        amount_max=payload.amount_max,
        documents_required=payload.documents_required,
        actor_id=authorized.id,
    )
    return _to_response(product)


@router.post("/{product_id}/activate", response_model=LoanProductResponse)
async def activate_loan_product(
    product_id: uuid.UUID, authorized: CanManageLoanProducts, service: LoanProductServiceDep
) -> LoanProductResponse:
    product = await service.set_active(product_id, is_active=True, actor_id=authorized.id)
    return _to_response(product)


@router.post("/{product_id}/deactivate", response_model=LoanProductResponse)
async def deactivate_loan_product(
    product_id: uuid.UUID, authorized: CanManageLoanProducts, service: LoanProductServiceDep
) -> LoanProductResponse:
    product = await service.set_active(product_id, is_active=False, actor_id=authorized.id)
    return _to_response(product)
