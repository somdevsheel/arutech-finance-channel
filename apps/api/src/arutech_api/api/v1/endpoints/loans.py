import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from arutech_api.api.deps import (
    CurrentUser,
    get_loan_application_service,
    get_loan_document_service,
    require_permission,
)
from arutech_api.api.v1.schemas.loans import (
    AssignRequest,
    CloseRequest,
    CommissionStatusUpdateRequest,
    DisburseRequest,
    DocumentReviewRequest,
    KycStatusUpdateRequest,
    LoanAnalyticsResponse,
    LoanApplicationCreateRequest,
    LoanApplicationResponse,
    LoanDocumentResponse,
    RejectRequest,
    SanctionRequest,
    VerificationStatusUpdateRequest,
)
from arutech_api.core.exceptions import ForbiddenError
from arutech_api.domain.loans.entities import (
    LoanApplicationEntity,
    LoanApplicationStatus,
    LoanDocumentEntity,
)
from arutech_api.domain.users.entities import UserEntity, UserRole
from arutech_api.services.loan_application_service import LoanApplicationService
from arutech_api.services.loan_document_service import LoanDocumentService

router = APIRouter(prefix="/loan-applications", tags=["loans"])

LoanApplicationServiceDep = Annotated[LoanApplicationService, Depends(get_loan_application_service)]
LoanDocumentServiceDep = Annotated[LoanDocumentService, Depends(get_loan_document_service)]
CanReadLoans = Annotated[UserEntity, Depends(require_permission("loans.read"))]
CanManageLoans = Annotated[UserEntity, Depends(require_permission("loans.manage"))]


def _application_response(application: LoanApplicationEntity) -> LoanApplicationResponse:
    return LoanApplicationResponse(
        id=application.id,
        customer_user_id=application.customer_user_id,
        lead_id=application.lead_id,
        loan_product_slug=application.loan_product_slug,
        requested_amount=application.requested_amount,
        tenure_months=application.tenure_months,
        interest_rate=application.interest_rate,
        monthly_income=application.monthly_income,
        existing_monthly_obligations=application.existing_monthly_obligations,
        status=application.status,
        kyc_status=application.kyc_status,
        verification_status=application.verification_status,
        eligibility_status=application.eligibility_status,
        credit_score=application.credit_score,
        risk_category=application.risk_category,
        assigned_to=application.assigned_to,
        rejection_reason=application.rejection_reason,
        sanctioned_amount=application.sanctioned_amount,
        sanctioned_tenure_months=application.sanctioned_tenure_months,
        sanction_date=application.sanction_date,
        disbursed_amount=application.disbursed_amount,
        disbursement_date=application.disbursement_date,
        disbursement_reference=application.disbursement_reference,
        commission_amount=application.commission_amount,
        commission_status=application.commission_status,
        closure_date=application.closure_date,
        closure_reason=application.closure_reason,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def _document_response(document: LoanDocumentEntity) -> LoanDocumentResponse:
    return LoanDocumentResponse(
        id=document.id,
        application_id=document.application_id,
        document_type=document.document_type,
        status=document.status,
        notes=document.notes,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _require_customer(current_user: UserEntity) -> uuid.UUID:
    if current_user.role != UserRole.CUSTOMER:
        raise ForbiddenError("Only customer accounts can manage their own loan applications")
    return current_user.id


# --- Customer self-service: CurrentUser only, ownership enforced in the
# service layer (get_own raises 404, never 403, for someone else's
# application — see LoanApplicationService.get_own's docstring). ---


@router.post("", response_model=LoanApplicationResponse)
async def create_application(
    payload: LoanApplicationCreateRequest,
    current_user: CurrentUser,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    customer_id = _require_customer(current_user)
    application = await application_service.create_draft(
        customer_user_id=customer_id,
        loan_product_slug=payload.loan_product_slug,
        requested_amount=payload.requested_amount,
        tenure_months=payload.tenure_months,
        monthly_income=payload.monthly_income,
        existing_monthly_obligations=payload.existing_monthly_obligations,
        interest_rate=payload.interest_rate,
        lead_id=payload.lead_id,
    )
    return _application_response(application)


@router.get("/mine", response_model=list[LoanApplicationResponse])
async def list_own_applications(
    current_user: CurrentUser, application_service: LoanApplicationServiceDep
) -> list[LoanApplicationResponse]:
    customer_id = _require_customer(current_user)
    applications = await application_service.list_own(customer_id)
    return [_application_response(application) for application in applications]


@router.get("/mine/{application_id}", response_model=LoanApplicationResponse)
async def get_own_application(
    application_id: uuid.UUID,
    current_user: CurrentUser,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    customer_id = _require_customer(current_user)
    application = await application_service.get_own(application_id, customer_id)
    return _application_response(application)


@router.post("/mine/{application_id}/submit", response_model=LoanApplicationResponse)
async def submit_application(
    application_id: uuid.UUID,
    current_user: CurrentUser,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    customer_id = _require_customer(current_user)
    application = await application_service.submit(application_id, customer_id)
    return _application_response(application)


@router.post("/mine/{application_id}/withdraw", response_model=LoanApplicationResponse)
async def withdraw_application(
    application_id: uuid.UUID,
    current_user: CurrentUser,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    customer_id = _require_customer(current_user)
    application = await application_service.withdraw(application_id, customer_id)
    return _application_response(application)


@router.get("/mine/{application_id}/documents", response_model=list[LoanDocumentResponse])
async def list_own_documents(
    application_id: uuid.UUID,
    current_user: CurrentUser,
    application_service: LoanApplicationServiceDep,
    document_service: LoanDocumentServiceDep,
) -> list[LoanDocumentResponse]:
    customer_id = _require_customer(current_user)
    await application_service.get_own(application_id, customer_id)  # 404s if not theirs
    documents = await document_service.list_for_application(application_id)
    return [_document_response(document) for document in documents]


@router.post(
    "/mine/{application_id}/documents/{document_id}/submit", response_model=LoanDocumentResponse
)
async def submit_own_document(
    application_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser,
    document_service: LoanDocumentServiceDep,
) -> LoanDocumentResponse:
    customer_id = _require_customer(current_user)
    document = await document_service.submit_own(
        application_id=application_id, document_id=document_id, customer_user_id=customer_id
    )
    return _document_response(document)


# --- Staff: loans.read / loans.manage ---


@router.get("", response_model=list[LoanApplicationResponse])
async def list_applications(
    _authorized: CanReadLoans,
    application_service: LoanApplicationServiceDep,
    status: LoanApplicationStatus | None = None,
    assigned_to: uuid.UUID | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[LoanApplicationResponse]:
    applications = await application_service.list_applications(
        status=status, assigned_to=assigned_to, limit=limit, offset=offset
    )
    return [_application_response(application) for application in applications]


@router.get("/analytics/summary", response_model=LoanAnalyticsResponse)
async def loan_analytics_summary(
    _authorized: CanReadLoans, application_service: LoanApplicationServiceDep
) -> LoanAnalyticsResponse:
    summary = await application_service.get_analytics_summary()
    return LoanAnalyticsResponse(
        total_applications=summary.total_applications,
        by_status=summary.by_status,
        by_product=summary.by_product,
        total_disbursed_amount=summary.total_disbursed_amount,
        total_commission_amount=summary.total_commission_amount,
    )


@router.get("/{application_id}", response_model=LoanApplicationResponse)
async def get_application(
    application_id: uuid.UUID,
    _authorized: CanReadLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.get_application(application_id)
    return _application_response(application)


@router.post("/{application_id}/assign", response_model=LoanApplicationResponse)
async def assign_application(
    application_id: uuid.UUID,
    payload: AssignRequest,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.assign(
        application_id=application_id, assignee_id=payload.assignee_id, actor_id=authorized.id
    )
    return _application_response(application)


@router.post("/{application_id}/kyc", response_model=LoanApplicationResponse)
async def update_kyc(
    application_id: uuid.UUID,
    payload: KycStatusUpdateRequest,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.update_kyc_status(
        application_id=application_id, status=payload.status, actor_id=authorized.id
    )
    return _application_response(application)


@router.post("/{application_id}/verification", response_model=LoanApplicationResponse)
async def update_verification(
    application_id: uuid.UUID,
    payload: VerificationStatusUpdateRequest,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.update_verification_status(
        application_id=application_id, status=payload.status, actor_id=authorized.id
    )
    return _application_response(application)


@router.post("/{application_id}/approve", response_model=LoanApplicationResponse)
async def approve_application(
    application_id: uuid.UUID,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.approve(
        application_id=application_id, actor_id=authorized.id
    )
    return _application_response(application)


@router.post("/{application_id}/reject", response_model=LoanApplicationResponse)
async def reject_application(
    application_id: uuid.UUID,
    payload: RejectRequest,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.reject(
        application_id=application_id, reason=payload.reason, actor_id=authorized.id
    )
    return _application_response(application)


@router.post("/{application_id}/sanction", response_model=LoanApplicationResponse)
async def sanction_application(
    application_id: uuid.UUID,
    payload: SanctionRequest,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.sanction(
        application_id=application_id,
        sanctioned_amount=payload.sanctioned_amount,
        sanctioned_tenure_months=payload.sanctioned_tenure_months,
        actor_id=authorized.id,
    )
    return _application_response(application)


@router.post("/{application_id}/disburse", response_model=LoanApplicationResponse)
async def disburse_application(
    application_id: uuid.UUID,
    payload: DisburseRequest,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.disburse(
        application_id=application_id,
        disbursement_reference=payload.disbursement_reference,
        actor_id=authorized.id,
    )
    return _application_response(application)


@router.post("/{application_id}/commission", response_model=LoanApplicationResponse)
async def update_commission(
    application_id: uuid.UUID,
    payload: CommissionStatusUpdateRequest,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.update_commission_status(
        application_id=application_id, status=payload.status, actor_id=authorized.id
    )
    return _application_response(application)


@router.post("/{application_id}/close", response_model=LoanApplicationResponse)
async def close_application(
    application_id: uuid.UUID,
    payload: CloseRequest,
    authorized: CanManageLoans,
    application_service: LoanApplicationServiceDep,
) -> LoanApplicationResponse:
    application = await application_service.close(
        application_id=application_id, closure_reason=payload.closure_reason, actor_id=authorized.id
    )
    return _application_response(application)


@router.get("/{application_id}/documents", response_model=list[LoanDocumentResponse])
async def list_documents(
    application_id: uuid.UUID, _authorized: CanReadLoans, document_service: LoanDocumentServiceDep
) -> list[LoanDocumentResponse]:
    documents = await document_service.list_for_application(application_id)
    return [_document_response(document) for document in documents]


@router.post(
    "/{application_id}/documents/{document_id}/review", response_model=LoanDocumentResponse
)
async def review_document(
    application_id: uuid.UUID,
    document_id: uuid.UUID,
    payload: DocumentReviewRequest,
    authorized: CanManageLoans,
    document_service: LoanDocumentServiceDep,
) -> LoanDocumentResponse:
    del application_id  # part of the URL for symmetry with list_documents; not needed to review
    document = await document_service.review(
        document_id=document_id,
        status=payload.status,
        notes=payload.notes,
        actor_id=authorized.id,
    )
    return _document_response(document)
