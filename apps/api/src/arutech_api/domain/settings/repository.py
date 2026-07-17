from abc import ABC, abstractmethod

from arutech_api.domain.settings.entities import SystemSettingEntity


class SystemSettingRepository(ABC):
    @abstractmethod
    async def get_by_key(self, key: str) -> SystemSettingEntity | None: ...

    @abstractmethod
    async def list_settings(self) -> list[SystemSettingEntity]: ...

    @abstractmethod
    async def set_value(self, key: str, value: str) -> SystemSettingEntity:
        """Updates an existing setting's value — settings are seeded by
        migration (see the Phase 9 migration), not created through the
        API; there's no legitimate "invent a new setting key at runtime"
        use case, the same reasoning `RbacRepository.list_permissions`
        applies to permission codes."""
        ...
