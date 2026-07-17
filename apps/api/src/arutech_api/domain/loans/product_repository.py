import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.loans.product_entities import LoanProductEntity


class LoanProductRepository(ABC):
    @abstractmethod
    async def create(self, product: LoanProductEntity) -> LoanProductEntity: ...

    @abstractmethod
    async def get_by_id(self, product_id: uuid.UUID) -> LoanProductEntity | None: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> LoanProductEntity | None:
        """The hot path: `LoanApplicationService.create_draft` and
        `_seed_document_checklist` call this on every application create/
        submit, the same call sites that used to do a dict lookup against
        `products.py`'s `LOAN_PRODUCTS`."""
        ...

    @abstractmethod
    async def list_products(self, *, is_active: bool | None = None) -> list[LoanProductEntity]: ...

    @abstractmethod
    async def update(self, product: LoanProductEntity) -> LoanProductEntity: ...

    @abstractmethod
    async def set_active(self, product_id: uuid.UUID, *, is_active: bool) -> LoanProductEntity: ...
