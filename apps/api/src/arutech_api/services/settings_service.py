import uuid

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.settings.entities import (
    SettingValueType,
    SystemSettingEntity,
    parse_bool_setting,
)
from arutech_api.domain.settings.repository import SystemSettingRepository
from arutech_api.services.audit_service import AuditService

_ENTITY_TYPE = "system_setting"


class SettingsService:
    """Phase 9's "Settings"/"Feature Flags"/"Workflow Management" — see
    `SystemSettingEntity`'s docstring for why these are one mechanism.
    `get_bool` is what other services call to read a toggle (see
    `LeadService._auto_assign`); the rest is the admin CRUD surface."""

    def __init__(self, settings_repo: SystemSettingRepository, audit_service: AuditService):
        self._settings_repo = settings_repo
        self._audit_service = audit_service

    async def get_bool(self, key: str, *, default: bool) -> bool:
        setting = await self._settings_repo.get_by_key(key)
        if setting is None:
            return default
        return parse_bool_setting(setting.value)

    async def list_settings(self) -> list[SystemSettingEntity]:
        return await self._settings_repo.list_settings()

    async def get_setting(self, key: str) -> SystemSettingEntity:
        setting = await self._settings_repo.get_by_key(key)
        if setting is None:
            raise NotFoundError(f"Setting '{key}' not found")
        return setting

    async def update_setting(
        self, key: str, value: str, *, actor_id: uuid.UUID
    ) -> SystemSettingEntity:
        setting = await self.get_setting(key)  # 404s if unknown
        _validate_value(value, setting.value_type)
        updated = await self._settings_repo.set_value(key, value)
        await self._audit_service.record(
            action="setting.updated",
            entity_type=_ENTITY_TYPE,
            entity_id=key,
            actor_id=actor_id,
            metadata={"value": value},
        )
        return updated


_FALSE_VALUES = frozenset({"false", "0", "no"})


def _validate_value(value: str, value_type: SettingValueType) -> None:
    normalized = value.strip().lower()
    if value_type is SettingValueType.BOOLEAN and not (
        parse_bool_setting(value) or normalized in _FALSE_VALUES
    ):
        raise ConflictError(f"'{value}' is not a valid boolean value")
    if value_type is SettingValueType.NUMBER:
        try:
            float(value)
        except ValueError as exc:
            raise ConflictError(f"'{value}' is not a valid number") from exc
