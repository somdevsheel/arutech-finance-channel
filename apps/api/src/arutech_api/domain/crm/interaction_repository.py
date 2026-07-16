import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.crm.entities import InteractionChannel, InteractionEntity


class InteractionRepository(ABC):
    @abstractmethod
    async def create(self, interaction: InteractionEntity) -> InteractionEntity: ...

    @abstractmethod
    async def list_for_customer(
        self, customer_user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[InteractionEntity]: ...

    @abstractmethod
    async def get_channel_counts(self) -> dict[InteractionChannel, int]:
        """Interaction count per channel, across all customers — the
        input to CustomerService's analytics summary. Total interaction
        count is the sum of these, so there's no separate method for it."""
        ...
