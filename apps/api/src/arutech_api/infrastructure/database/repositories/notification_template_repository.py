import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.notifications.entities import (
    NotificationChannel,
    NotificationTemplateEntity,
)
from arutech_api.domain.notifications.repository import NotificationTemplateRepository
from arutech_api.infrastructure.database.models.notifications import NotificationTemplate


def _to_entity(model: NotificationTemplate) -> NotificationTemplateEntity:
    return NotificationTemplateEntity(
        id=model.id,
        code=model.code,
        channel=model.channel,
        subject=model.subject,
        body=model.body,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyNotificationTemplateRepository(NotificationTemplateRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, template: NotificationTemplateEntity) -> NotificationTemplateEntity:
        model = NotificationTemplate(
            id=template.id,
            code=template.code,
            channel=template.channel,
            subject=template.subject,
            body=template.body,
            is_active=template.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, template_id: uuid.UUID) -> NotificationTemplateEntity | None:
        model = await self._session.get(NotificationTemplate, template_id)
        return _to_entity(model) if model else None

    async def get_by_code(self, code: str) -> NotificationTemplateEntity | None:
        result = await self._session.execute(
            select(NotificationTemplate).where(NotificationTemplate.code == code)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_templates(
        self,
        *,
        channel: NotificationChannel | None = None,
        is_active: bool | None = None,
    ) -> list[NotificationTemplateEntity]:
        query = select(NotificationTemplate)
        if channel is not None:
            query = query.where(NotificationTemplate.channel == channel)
        if is_active is not None:
            query = query.where(NotificationTemplate.is_active.is_(is_active))
        result = await self._session.execute(query.order_by(NotificationTemplate.code))
        return [_to_entity(model) for model in result.scalars().all()]

    async def update(self, template: NotificationTemplateEntity) -> NotificationTemplateEntity:
        model = await self._session.get(NotificationTemplate, template.id)
        if model is None:
            raise NotFoundError(f"Notification template {template.id} not found")

        model.subject = template.subject
        model.body = template.body
        model.is_active = template.is_active

        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def set_active(
        self, template_id: uuid.UUID, *, is_active: bool
    ) -> NotificationTemplateEntity:
        model = await self._session.get(NotificationTemplate, template_id)
        if model is None:
            raise NotFoundError(f"Notification template {template_id} not found")
        model.is_active = is_active
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
