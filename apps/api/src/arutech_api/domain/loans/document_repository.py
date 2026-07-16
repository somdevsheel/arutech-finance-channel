import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.loans.entities import LoanDocumentEntity, LoanDocumentStatus


class LoanDocumentRepository(ABC):
    @abstractmethod
    async def create(self, document: LoanDocumentEntity) -> LoanDocumentEntity: ...

    @abstractmethod
    async def get_by_id(self, document_id: uuid.UUID) -> LoanDocumentEntity | None: ...

    @abstractmethod
    async def list_for_application(self, application_id: uuid.UUID) -> list[LoanDocumentEntity]: ...

    @abstractmethod
    async def update_status(
        self, document_id: uuid.UUID, status: LoanDocumentStatus, notes: str | None
    ) -> LoanDocumentEntity: ...
