from abc import ABC, abstractmethod

from arutech_api.domain.audit.entities import AuditLogEntity


class AuditLogRepository(ABC):
    @abstractmethod
    async def record(self, entry: AuditLogEntity) -> AuditLogEntity: ...

    @abstractmethod
    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[AuditLogEntity]: ...

    @abstractmethod
    async def list_for_entity(self, entity_type: str, entity_id: str) -> list[AuditLogEntity]:
        """Every audit entry for one specific entity, oldest first — the
        activity timeline a lead (or any future audited entity) needs."""
        ...
