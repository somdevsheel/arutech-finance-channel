import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from arutech_api.api.deps import get_notification_template_service, require_permission
from arutech_api.api.v1.schemas.notification_templates import (
    NotificationTemplateCreateRequest,
    NotificationTemplateResponse,
    NotificationTemplateUpdateRequest,
)
from arutech_api.domain.notifications.entities import (
    NotificationChannel,
    NotificationTemplateEntity,
)
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.notification_template_service import NotificationTemplateService

router = APIRouter(prefix="/notification-templates", tags=["notification-templates"])

NotificationTemplateServiceDep = Annotated[
    NotificationTemplateService, Depends(get_notification_template_service)
]
CanReadTemplates = Annotated[
    UserEntity, Depends(require_permission("notification_templates.read"))
]
CanManageTemplates = Annotated[
    UserEntity, Depends(require_permission("notification_templates.manage"))
]


def _to_response(template: NotificationTemplateEntity) -> NotificationTemplateResponse:
    return NotificationTemplateResponse(
        id=template.id,
        code=template.code,
        channel=template.channel,
        subject=template.subject,
        body=template.body,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("", response_model=list[NotificationTemplateResponse])
async def list_templates(
    _authorized: CanReadTemplates,
    service: NotificationTemplateServiceDep,
    channel: NotificationChannel | None = None,
    is_active: bool | None = None,
) -> list[NotificationTemplateResponse]:
    templates = await service.list_templates(channel=channel, is_active=is_active)
    return [_to_response(template) for template in templates]


@router.post("", response_model=NotificationTemplateResponse)
async def create_template(
    payload: NotificationTemplateCreateRequest,
    authorized: CanManageTemplates,
    service: NotificationTemplateServiceDep,
) -> NotificationTemplateResponse:
    template = await service.create_template(
        code=payload.code,
        channel=payload.channel,
        subject=payload.subject,
        body=payload.body,
        actor_id=authorized.id,
    )
    return _to_response(template)


@router.get("/{template_id}", response_model=NotificationTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    _authorized: CanReadTemplates,
    service: NotificationTemplateServiceDep,
) -> NotificationTemplateResponse:
    template = await service.get_template(template_id)
    return _to_response(template)


@router.put("/{template_id}", response_model=NotificationTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    payload: NotificationTemplateUpdateRequest,
    authorized: CanManageTemplates,
    service: NotificationTemplateServiceDep,
) -> NotificationTemplateResponse:
    template = await service.update_template(
        template_id, subject=payload.subject, body=payload.body, actor_id=authorized.id
    )
    return _to_response(template)


@router.post("/{template_id}/activate", response_model=NotificationTemplateResponse)
async def activate_template(
    template_id: uuid.UUID,
    authorized: CanManageTemplates,
    service: NotificationTemplateServiceDep,
) -> NotificationTemplateResponse:
    template = await service.set_active(template_id, is_active=True, actor_id=authorized.id)
    return _to_response(template)


@router.post("/{template_id}/deactivate", response_model=NotificationTemplateResponse)
async def deactivate_template(
    template_id: uuid.UUID,
    authorized: CanManageTemplates,
    service: NotificationTemplateServiceDep,
) -> NotificationTemplateResponse:
    template = await service.set_active(template_id, is_active=False, actor_id=authorized.id)
    return _to_response(template)
