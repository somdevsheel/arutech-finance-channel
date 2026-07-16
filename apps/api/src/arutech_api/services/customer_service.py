import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.audit.repository import AuditLogRepository
from arutech_api.domain.crm.entities import (
    CustomerAnalyticsSummary,
    CustomerProfileEntity,
    CustomerSegment,
)
from arutech_api.domain.crm.interaction_repository import InteractionRepository
from arutech_api.domain.crm.repository import CustomerRepository
from arutech_api.domain.users.entities import UserRole
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService

_ENTITY_TYPE = "customer"


@dataclass(frozen=True, slots=True)
class CustomerTimelineEntry:
    occurred_at: datetime
    kind: str  # "interaction" | "audit"
    summary: str
    detail: dict[str, Any] | None


class CustomerService:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        interaction_repo: InteractionRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
        audit_repo: AuditLogRepository,
    ):
        self._customer_repo = customer_repo
        self._interaction_repo = interaction_repo
        self._user_repo = user_repo
        self._audit_service = audit_service
        self._audit_repo = audit_repo

    async def _require_customer(self, user_id: uuid.UUID) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Customer not found")
        if user.role != UserRole.CUSTOMER:
            raise ConflictError("User is not a customer")

    async def get_profile(self, user_id: uuid.UUID) -> CustomerProfileEntity:
        """Customer 360: lazily materializes a profile on first touch, so
        Phase 6 never has to reach back into Phase 2's registration flow
        to pre-create one for every signup."""
        await self._require_customer(user_id)
        return await self._customer_repo.get_or_create_profile(user_id)

    async def list_customers(
        self,
        *,
        segment: CustomerSegment | None = None,
        tag: str | None = None,
        relationship_manager_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CustomerProfileEntity]:
        return await self._customer_repo.list_profiles(
            segment=segment,
            tag=tag,
            relationship_manager_id=relationship_manager_id,
            limit=limit,
            offset=offset,
        )

    async def set_relationship_manager(
        self, *, user_id: uuid.UUID, relationship_manager_id: uuid.UUID, actor_id: uuid.UUID
    ) -> CustomerProfileEntity:
        await self._require_customer(user_id)
        await self._customer_repo.get_or_create_profile(user_id)

        rm = await self._user_repo.get_by_id(relationship_manager_id)
        if rm is None:
            raise NotFoundError("Relationship manager not found")
        if rm.role not in (UserRole.EMPLOYEE, UserRole.ADMIN):
            raise ConflictError("Relationship manager must be an employee or admin")

        updated = await self._customer_repo.set_relationship_manager(
            user_id, relationship_manager_id
        )
        await self._audit_service.record(
            action="customer.relationship_manager_changed",
            entity_type=_ENTITY_TYPE,
            entity_id=str(user_id),
            actor_id=actor_id,
            metadata={"relationship_manager_id": str(relationship_manager_id)},
        )
        return updated

    async def set_segment(
        self, *, user_id: uuid.UUID, segment: CustomerSegment, actor_id: uuid.UUID
    ) -> CustomerProfileEntity:
        await self._require_customer(user_id)
        await self._customer_repo.get_or_create_profile(user_id)

        updated = await self._customer_repo.set_segment(user_id, segment)
        await self._audit_service.record(
            action="customer.segment_changed",
            entity_type=_ENTITY_TYPE,
            entity_id=str(user_id),
            actor_id=actor_id,
            metadata={"segment": segment.value},
        )
        return updated

    async def add_tag(
        self, *, user_id: uuid.UUID, tag_name: str, actor_id: uuid.UUID
    ) -> CustomerProfileEntity:
        await self._require_customer(user_id)
        await self._customer_repo.get_or_create_profile(user_id)

        updated = await self._customer_repo.add_tag(user_id, tag_name)
        await self._audit_service.record(
            action="customer.tag_added",
            entity_type=_ENTITY_TYPE,
            entity_id=str(user_id),
            actor_id=actor_id,
            metadata={"tag": tag_name},
        )
        return updated

    async def remove_tag(
        self, *, user_id: uuid.UUID, tag_name: str, actor_id: uuid.UUID
    ) -> CustomerProfileEntity:
        await self._require_customer(user_id)
        await self._customer_repo.get_or_create_profile(user_id)

        updated = await self._customer_repo.remove_tag(user_id, tag_name)
        await self._audit_service.record(
            action="customer.tag_removed",
            entity_type=_ENTITY_TYPE,
            entity_id=str(user_id),
            actor_id=actor_id,
            metadata={"tag": tag_name},
        )
        return updated

    async def list_all_tags(self) -> list[str]:
        return await self._customer_repo.list_all_tags()

    async def get_analytics_summary(self) -> CustomerAnalyticsSummary:
        total = await self._customer_repo.count_total()
        by_segment = await self._customer_repo.count_by_segment()
        without_rm = await self._customer_repo.count_without_relationship_manager()
        by_channel = await self._interaction_repo.get_channel_counts()

        return CustomerAnalyticsSummary(
            total_customers=total,
            by_segment=by_segment,
            customers_without_relationship_manager=without_rm,
            total_interactions=sum(by_channel.values()),
            by_channel=by_channel,
        )

    async def get_timeline(self, user_id: uuid.UUID) -> list[CustomerTimelineEntry]:
        await self._require_customer(user_id)

        audit_entries = await self._audit_repo.list_for_entity(_ENTITY_TYPE, str(user_id))
        interactions = await self._interaction_repo.list_for_customer(user_id, limit=1_000)

        entries = [
            CustomerTimelineEntry(
                occurred_at=entry.created_at or datetime.min,
                kind="audit",
                summary=entry.action,
                detail=entry.extra_metadata,
            )
            for entry in audit_entries
        ] + [
            CustomerTimelineEntry(
                occurred_at=interaction.occurred_at or datetime.min,
                kind="interaction",
                summary=interaction.summary,
                detail={
                    "channel": interaction.channel.value,
                    "direction": interaction.direction.value,
                    "notes": interaction.notes,
                },
            )
            for interaction in interactions
        ]
        return sorted(entries, key=lambda e: e.occurred_at)
