from abc import ABC, abstractmethod

from arutech_api.domain.contact.entities import ContactSubmissionEntity


class ContactSubmissionRepository(ABC):
    @abstractmethod
    async def create(self, submission: ContactSubmissionEntity) -> ContactSubmissionEntity: ...
