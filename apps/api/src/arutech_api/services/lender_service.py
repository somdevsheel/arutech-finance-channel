import dataclasses
import uuid
from decimal import Decimal

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.lenders.entities import LenderEntity, LenderType
from arutech_api.domain.lenders.repository import LenderRepository
from arutech_api.services.audit_service import AuditService

_ENTITY_TYPE = "lender"


class LenderService:
    def __init__(self, lender_repo: LenderRepository, audit_service: AuditService):
        self._lender_repo = lender_repo
        self._audit_service = audit_service

    async def get_lender(self, lender_id: uuid.UUID) -> LenderEntity:
        lender = await self._lender_repo.get_by_id(lender_id)
        if lender is None:
            raise NotFoundError(f"Lender {lender_id} not found")
        return lender

    async def list_lenders(
        self,
        *,
        type: LenderType | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LenderEntity]:
        return await self._lender_repo.list_lenders(
            type=type, is_active=is_active, limit=limit, offset=offset
        )

    async def create_lender(
        self,
        *,
        name: str,
        type: LenderType,
        code: str,
        contact_email: str | None,
        contact_phone: str | None,
        commission_rate_percent: Decimal,
        actor_id: uuid.UUID,
    ) -> LenderEntity:
        if await self._lender_repo.get_by_code(code) is not None:
            raise ConflictError(f"A lender with code '{code}' already exists")

        lender = await self._lender_repo.create(
            LenderEntity(
                name=name,
                type=type,
                code=code,
                contact_email=contact_email,
                contact_phone=contact_phone,
                commission_rate_percent=commission_rate_percent,
            )
        )
        await self._audit_service.record(
            action="lender.created", entity_type=_ENTITY_TYPE, entity_id=str(lender.id),
            actor_id=actor_id,
        )
        return lender

    async def update_lender(
        self,
        lender_id: uuid.UUID,
        *,
        name: str,
        contact_email: str | None,
        contact_phone: str | None,
        commission_rate_percent: Decimal,
        actor_id: uuid.UUID,
    ) -> LenderEntity:
        lender = await self.get_lender(lender_id)
        updated = dataclasses.replace(
            lender,
            name=name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            commission_rate_percent=commission_rate_percent,
        )
        saved = await self._lender_repo.update(updated)
        await self._audit_service.record(
            action="lender.updated", entity_type=_ENTITY_TYPE, entity_id=str(lender_id),
            actor_id=actor_id,
        )
        return saved

    async def set_active(
        self, lender_id: uuid.UUID, *, is_active: bool, actor_id: uuid.UUID
    ) -> LenderEntity:
        await self.get_lender(lender_id)  # 404s if unknown
        updated = await self._lender_repo.set_active(lender_id, is_active=is_active)
        await self._audit_service.record(
            action="lender.activated" if is_active else "lender.deactivated",
            entity_type=_ENTITY_TYPE,
            entity_id=str(lender_id),
            actor_id=actor_id,
        )
        return updated
