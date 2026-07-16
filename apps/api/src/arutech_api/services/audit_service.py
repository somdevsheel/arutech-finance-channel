import uuid
from typing import Any

from arutech_api.domain.audit.entities import AuditLogEntity
from arutech_api.domain.audit.repository import AuditLogRepository


class AuditService:
    def __init__(self, audit_repo: AuditLogRepository):
        self._audit_repo = audit_repo

    async def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self._audit_repo.record(
            AuditLogEntity(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
                extra_metadata=metadata,
            )
        )

    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[AuditLogEntity]:
        return await self._audit_repo.list_recent(limit=limit, offset=offset)
