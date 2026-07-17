from typing import Annotated

from fastapi import APIRouter, Depends

from arutech_api.api.deps import get_settings_service, require_permission
from arutech_api.api.v1.schemas.settings import SystemSettingResponse, SystemSettingUpdateRequest
from arutech_api.domain.settings.entities import SystemSettingEntity
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.settings_service import SettingsService

router = APIRouter(prefix="/admin/settings", tags=["settings"])

SettingsServiceDep = Annotated[SettingsService, Depends(get_settings_service)]
CanReadSettings = Annotated[UserEntity, Depends(require_permission("settings.read"))]
CanManageSettings = Annotated[UserEntity, Depends(require_permission("settings.manage"))]


def _to_response(setting: SystemSettingEntity) -> SystemSettingResponse:
    return SystemSettingResponse(
        id=setting.id,
        key=setting.key,
        value=setting.value,
        value_type=setting.value_type,
        description=setting.description,
        updated_at=setting.updated_at,
    )


@router.get("", response_model=list[SystemSettingResponse])
async def list_settings(
    _authorized: CanReadSettings, service: SettingsServiceDep
) -> list[SystemSettingResponse]:
    settings = await service.list_settings()
    return [_to_response(setting) for setting in settings]


@router.get("/{key}", response_model=SystemSettingResponse)
async def get_setting(
    key: str, _authorized: CanReadSettings, service: SettingsServiceDep
) -> SystemSettingResponse:
    setting = await service.get_setting(key)
    return _to_response(setting)


@router.put("/{key}", response_model=SystemSettingResponse)
async def update_setting(
    key: str,
    payload: SystemSettingUpdateRequest,
    authorized: CanManageSettings,
    service: SettingsServiceDep,
) -> SystemSettingResponse:
    setting = await service.update_setting(key, payload.value, actor_id=authorized.id)
    return _to_response(setting)
