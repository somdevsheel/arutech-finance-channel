import uuid
from abc import ABC, abstractmethod

from arutech_api.domain.cms.entities import BlogPostEntity


class BlogPostRepository(ABC):
    @abstractmethod
    async def create(self, post: BlogPostEntity) -> BlogPostEntity: ...

    @abstractmethod
    async def get_by_id(self, post_id: uuid.UUID) -> BlogPostEntity | None: ...

    @abstractmethod
    async def get_by_slug(
        self, slug: str, *, published_only: bool = False
    ) -> BlogPostEntity | None:
        """`published_only=True` is what the public routes use — a draft
        or unpublished post 404s for a visitor even if they somehow
        guess its slug, the same "don't confirm existence" reasoning
        Phase 7's `get_own` docstring gives for a 404-not-403 choice."""
        ...

    @abstractmethod
    async def list_posts(
        self, *, published_only: bool = False, limit: int = 50, offset: int = 0
    ) -> list[BlogPostEntity]: ...

    @abstractmethod
    async def update(self, post: BlogPostEntity) -> BlogPostEntity: ...

    @abstractmethod
    async def set_published(
        self, post_id: uuid.UUID, *, is_published: bool
    ) -> BlogPostEntity: ...

    @abstractmethod
    async def delete(self, post_id: uuid.UUID) -> None: ...
