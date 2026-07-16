import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.crm.entities import CustomerProfileEntity, CustomerSegment


class CustomerRepository(ABC):
    @abstractmethod
    async def get_or_create_profile(self, user_id: uuid.UUID) -> CustomerProfileEntity: ...

    @abstractmethod
    async def get_profile(self, user_id: uuid.UUID) -> CustomerProfileEntity | None: ...

    @abstractmethod
    async def list_profiles(
        self,
        *,
        segment: CustomerSegment | None = None,
        tag: str | None = None,
        relationship_manager_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CustomerProfileEntity]: ...

    @abstractmethod
    async def set_relationship_manager(
        self, user_id: uuid.UUID, relationship_manager_id: uuid.UUID
    ) -> CustomerProfileEntity: ...

    @abstractmethod
    async def set_segment(
        self, user_id: uuid.UUID, segment: CustomerSegment
    ) -> CustomerProfileEntity: ...

    @abstractmethod
    async def add_tag(self, user_id: uuid.UUID, tag_name: str) -> CustomerProfileEntity: ...

    @abstractmethod
    async def remove_tag(self, user_id: uuid.UUID, tag_name: str) -> CustomerProfileEntity: ...

    @abstractmethod
    async def list_all_tags(self) -> list[str]: ...

    @abstractmethod
    async def count_total(self) -> int: ...

    @abstractmethod
    async def count_by_segment(self) -> dict[CustomerSegment, int]: ...

    @abstractmethod
    async def count_without_relationship_manager(self) -> int: ...
