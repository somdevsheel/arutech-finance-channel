import dataclasses
import uuid

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.notifications.entities import (
    NotificationChannel,
    NotificationTemplateEntity,
)
from arutech_api.domain.notifications.repository import NotificationTemplateRepository
from arutech_api.services.audit_service import AuditService

_ENTITY_TYPE = "notification_template"


class NotificationTemplateService:
    def __init__(
        self, template_repo: NotificationTemplateRepository, audit_service: AuditService
    ):
        self._template_repo = template_repo
        self._audit_service = audit_service

    async def get_template(self, template_id: uuid.UUID) -> NotificationTemplateEntity:
        template = await self._template_repo.get_by_id(template_id)
        if template is None:
            raise NotFoundError(f"Notification template {template_id} not found")
        return template

    async def list_templates(
        self,
        *,
        channel: NotificationChannel | None = None,
        is_active: bool | None = None,
    ) -> list[NotificationTemplateEntity]:
        return await self._template_repo.list_templates(channel=channel, is_active=is_active)

    async def create_template(
        self,
        *,
        code: str,
        channel: NotificationChannel,
        subject: str | None,
        body: str,
        actor_id: uuid.UUID,
    ) -> NotificationTemplateEntity:
        if await self._template_repo.get_by_code(code) is not None:
            raise ConflictError(f"A template with code '{code}' already exists")

        template = await self._template_repo.create(
            NotificationTemplateEntity(code=code, channel=channel, subject=subject, body=body)
        )
        await self._audit_service.record(
            action="notification_template.created",
            entity_type=_ENTITY_TYPE,
            entity_id=str(template.id),
            actor_id=actor_id,
        )
        return template

    async def update_template(
        self,
        template_id: uuid.UUID,
        *,
        subject: str | None,
        body: str,
        actor_id: uuid.UUID,
    ) -> NotificationTemplateEntity:
        template = await self.get_template(template_id)
        updated = dataclasses.replace(template, subject=subject, body=body)
        saved = await self._template_repo.update(updated)
        await self._audit_service.record(
            action="notification_template.updated",
            entity_type=_ENTITY_TYPE,
            entity_id=str(template_id),
            actor_id=actor_id,
        )
        return saved

    async def set_active(
        self, template_id: uuid.UUID, *, is_active: bool, actor_id: uuid.UUID
    ) -> NotificationTemplateEntity:
        await self.get_template(template_id)  # 404s if unknown
        updated = await self._template_repo.set_active(template_id, is_active=is_active)
        verb = "activated" if is_active else "deactivated"
        await self._audit_service.record(
            action=f"notification_template.{verb}",
            entity_type=_ENTITY_TYPE,
            entity_id=str(template_id),
            actor_id=actor_id,
        )
        return updated
