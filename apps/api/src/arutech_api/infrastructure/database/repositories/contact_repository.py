from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.domain.contact.entities import ContactSubmissionEntity
from arutech_api.domain.contact.repository import ContactSubmissionRepository
from arutech_api.infrastructure.database.models.contact import ContactSubmission


def _to_entity(model: ContactSubmission) -> ContactSubmissionEntity:
    return ContactSubmissionEntity(
        id=model.id,
        name=model.name,
        email=model.email,
        phone=model.phone,
        subject=model.subject,
        message=model.message,
        created_at=model.created_at,
    )


class SqlAlchemyContactSubmissionRepository(ContactSubmissionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, submission: ContactSubmissionEntity) -> ContactSubmissionEntity:
        model = ContactSubmission(
            id=submission.id,
            name=submission.name,
            email=submission.email,
            phone=submission.phone,
            subject=submission.subject,
            message=submission.message,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
