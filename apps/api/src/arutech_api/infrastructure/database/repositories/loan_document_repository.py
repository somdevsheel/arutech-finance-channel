import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.loans.document_repository import LoanDocumentRepository
from arutech_api.domain.loans.entities import LoanDocumentEntity, LoanDocumentStatus
from arutech_api.infrastructure.database.models.loans import LoanDocument


def _to_entity(model: LoanDocument) -> LoanDocumentEntity:
    return LoanDocumentEntity(
        id=model.id,
        application_id=model.application_id,
        document_type=model.document_type,
        status=model.status,
        notes=model.notes,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyLoanDocumentRepository(LoanDocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, document: LoanDocumentEntity) -> LoanDocumentEntity:
        model = LoanDocument(
            id=document.id,
            application_id=document.application_id,
            document_type=document.document_type,
            status=document.status,
            notes=document.notes,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, document_id: uuid.UUID) -> LoanDocumentEntity | None:
        result = await self._session.execute(
            select(LoanDocument).where(LoanDocument.id == document_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_for_application(self, application_id: uuid.UUID) -> list[LoanDocumentEntity]:
        result = await self._session.execute(
            select(LoanDocument)
            .where(LoanDocument.application_id == application_id)
            .order_by(LoanDocument.created_at)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def update_status(
        self, document_id: uuid.UUID, status: LoanDocumentStatus, notes: str | None
    ) -> LoanDocumentEntity:
        result = await self._session.execute(
            select(LoanDocument).where(LoanDocument.id == document_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError("Document not found")

        model.status = status
        if notes is not None:
            model.notes = notes
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
