from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.domain.audit.entities import AuditLogEntity
from arutech_api.domain.audit.repository import AuditLogRepository
from arutech_api.infrastructure.database.models.audit_log import AuditLog


def _to_entity(model: AuditLog) -> AuditLogEntity:
    return AuditLogEntity(
        id=model.id,
        actor_id=model.actor_id,
        action=model.action,
        entity_type=model.entity_type,
        entity_id=model.entity_id,
        extra_metadata=model.extra_metadata,
        created_at=model.created_at,
    )


class SqlAlchemyAuditLogRepository(AuditLogRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def record(self, entry: AuditLogEntity) -> AuditLogEntity:
        model = AuditLog(
            id=entry.id,
            actor_id=entry.actor_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            extra_metadata=entry.extra_metadata,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[AuditLogEntity]:
        result = await self._session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def list_for_entity(self, entity_type: str, entity_id: str) -> list[AuditLogEntity]:
        result = await self._session.execute(
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.created_at.asc())
        )
        return [_to_entity(model) for model in result.scalars().all()]
