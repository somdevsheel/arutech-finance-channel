import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.notifications.entities import (
    NotificationChannel,
    NotificationTemplateEntity,
)


class NotificationTemplateRepository(ABC):
    @abstractmethod
    async def create(self, template: NotificationTemplateEntity) -> NotificationTemplateEntity: ...

    @abstractmethod
    async def get_by_id(self, template_id: uuid.UUID) -> NotificationTemplateEntity | None: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> NotificationTemplateEntity | None: ...

    @abstractmethod
    async def list_templates(
        self,
        *,
        channel: NotificationChannel | None = None,
        is_active: bool | None = None,
    ) -> list[NotificationTemplateEntity]: ...

    @abstractmethod
    async def update(self, template: NotificationTemplateEntity) -> NotificationTemplateEntity: ...

    @abstractmethod
    async def set_active(
        self, template_id: uuid.UUID, *, is_active: bool
    ) -> NotificationTemplateEntity: ...
