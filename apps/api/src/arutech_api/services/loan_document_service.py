import uuid

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.loans.document_repository import LoanDocumentRepository
from arutech_api.domain.loans.entities import LoanDocumentEntity, LoanDocumentStatus
from arutech_api.domain.loans.repository import LoanApplicationRepository
from arutech_api.services.audit_service import AuditService


class LoanDocumentService:
    def __init__(
        self,
        document_repo: LoanDocumentRepository,
        application_repo: LoanApplicationRepository,
        audit_service: AuditService,
    ):
        self._document_repo = document_repo
        self._application_repo = application_repo
        self._audit_service = audit_service

    async def list_for_application(self, application_id: uuid.UUID) -> list[LoanDocumentEntity]:
        application = await self._application_repo.get_by_id(application_id)
        if application is None:
            raise NotFoundError("Loan application not found")
        return await self._document_repo.list_for_application(application_id)

    async def submit_own(
        self, *, application_id: uuid.UUID, document_id: uuid.UUID, customer_user_id: uuid.UUID
    ) -> LoanDocumentEntity:
        application = await self._application_repo.get_by_id(application_id)
        if application is None or application.customer_user_id != customer_user_id:
            raise NotFoundError("Loan application not found")

        document = await self._document_repo.get_by_id(document_id)
        if document is None or document.application_id != application_id:
            raise NotFoundError("Document not found")

        updated = await self._document_repo.update_status(
            document_id, LoanDocumentStatus.SUBMITTED, notes=None
        )
        await self._audit_service.record(
            action="loan_application.document_submitted",
            entity_type="loan_application",
            entity_id=str(application_id),
            actor_id=customer_user_id,
            metadata={"document_id": str(document_id), "document_type": document.document_type},
        )
        return updated

    async def review(
        self,
        *,
        document_id: uuid.UUID,
        status: LoanDocumentStatus,
        notes: str | None,
        actor_id: uuid.UUID,
    ) -> LoanDocumentEntity:
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise NotFoundError("Document not found")

        updated = await self._document_repo.update_status(document_id, status, notes)
        await self._audit_service.record(
            action="loan_application.document_reviewed",
            entity_type="loan_application",
            entity_id=str(document.application_id),
            actor_id=actor_id,
            metadata={
                "document_id": str(document_id),
                "status": status.value,
                "document_type": document.document_type,
            },
        )
        return updated
