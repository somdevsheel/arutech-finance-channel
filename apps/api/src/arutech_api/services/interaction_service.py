import uuid
from datetime import UTC, datetime

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.crm.entities import (
    InteractionChannel,
    InteractionDirection,
    InteractionEntity,
)
from arutech_api.domain.crm.interaction_repository import InteractionRepository
from arutech_api.domain.crm.repository import CustomerRepository
from arutech_api.domain.users.entities import UserRole
from arutech_api.domain.users.repository import UserRepository
from arutech_api.services.audit_service import AuditService


class InteractionService:
    def __init__(
        self,
        interaction_repo: InteractionRepository,
        customer_repo: CustomerRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
    ):
        self._interaction_repo = interaction_repo
        self._customer_repo = customer_repo
        self._user_repo = user_repo
        self._audit_service = audit_service

    async def log_interaction(
        self,
        *,
        customer_user_id: uuid.UUID,
        channel: InteractionChannel,
        summary: str,
        logged_by: uuid.UUID,
        direction: InteractionDirection = InteractionDirection.OUTBOUND,
        notes: str | None = None,
        occurred_at: datetime | None = None,
    ) -> InteractionEntity:
        customer = await self._user_repo.get_by_id(customer_user_id)
        if customer is None:
            raise NotFoundError("Customer not found")
        if customer.role != UserRole.CUSTOMER:
            raise ConflictError("User is not a customer")

        await self._customer_repo.get_or_create_profile(customer_user_id)

        interaction = await self._interaction_repo.create(
            InteractionEntity(
                customer_user_id=customer_user_id,
                channel=channel,
                direction=direction,
                summary=summary,
                notes=notes,
                logged_by=logged_by,
                occurred_at=occurred_at or datetime.now(UTC),
            )
        )
        await self._audit_service.record(
            action="customer.interaction_logged",
            entity_type="customer",
            entity_id=str(customer_user_id),
            actor_id=logged_by,
            metadata={"channel": channel.value, "interaction_id": str(interaction.id)},
        )
        return interaction

    async def list_for_customer(
        self, customer_user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[InteractionEntity]:
        customer = await self._user_repo.get_by_id(customer_user_id)
        if customer is None:
            raise NotFoundError("Customer not found")
        return await self._interaction_repo.list_for_customer(
            customer_user_id, limit=limit, offset=offset
        )
