import dataclasses
import uuid

from arutech_api.core.exceptions import ConflictError, NotFoundError
from arutech_api.domain.cms.entities import BlogPostEntity, BlogSection
from arutech_api.domain.cms.repository import BlogPostRepository
from arutech_api.services.audit_service import AuditService

_ENTITY_TYPE = "blog_post"


class BlogPostService:
    """Phase 9's "CMS" — scoped to blog posts. Public reads
    (`get_published_post`, `list_published_posts`) never return a draft;
    admin reads (`get_post`, `list_posts`) see everything, gated by
    `cms.read`/`cms.manage` at the router level, not here."""

    def __init__(self, post_repo: BlogPostRepository, audit_service: AuditService):
        self._post_repo = post_repo
        self._audit_service = audit_service

    async def get_post(self, post_id: uuid.UUID) -> BlogPostEntity:
        post = await self._post_repo.get_by_id(post_id)
        if post is None:
            raise NotFoundError(f"Blog post {post_id} not found")
        return post

    async def list_posts(self, *, limit: int = 50, offset: int = 0) -> list[BlogPostEntity]:
        return await self._post_repo.list_posts(published_only=False, limit=limit, offset=offset)

    async def get_published_post(self, slug: str) -> BlogPostEntity:
        post = await self._post_repo.get_by_slug(slug, published_only=True)
        if post is None:
            raise NotFoundError(f"Blog post '{slug}' not found")
        return post

    async def list_published_posts(
        self, *, limit: int = 50, offset: int = 0
    ) -> list[BlogPostEntity]:
        return await self._post_repo.list_posts(published_only=True, limit=limit, offset=offset)

    async def create_post(
        self,
        *,
        slug: str,
        title: str,
        excerpt: str,
        author: str,
        reading_minutes: int,
        sections: list[BlogSection],
        tags: list[str],
        actor_id: uuid.UUID,
    ) -> BlogPostEntity:
        if await self._post_repo.get_by_slug(slug) is not None:
            raise ConflictError(f"A blog post with slug '{slug}' already exists")

        post = await self._post_repo.create(
            BlogPostEntity(
                slug=slug,
                title=title,
                excerpt=excerpt,
                author=author,
                reading_minutes=reading_minutes,
                sections=tuple(sections),
                tags=tuple(tags),
            )
        )
        await self._audit_service.record(
            action="blog_post.created", entity_type=_ENTITY_TYPE, entity_id=str(post.id),
            actor_id=actor_id,
        )
        return post

    async def update_post(
        self,
        post_id: uuid.UUID,
        *,
        title: str,
        excerpt: str,
        author: str,
        reading_minutes: int,
        sections: list[BlogSection],
        tags: list[str],
        actor_id: uuid.UUID,
    ) -> BlogPostEntity:
        post = await self.get_post(post_id)
        updated = dataclasses.replace(
            post,
            title=title,
            excerpt=excerpt,
            author=author,
            reading_minutes=reading_minutes,
            sections=tuple(sections),
            tags=tuple(tags),
        )
        saved = await self._post_repo.update(updated)
        await self._audit_service.record(
            action="blog_post.updated", entity_type=_ENTITY_TYPE, entity_id=str(post_id),
            actor_id=actor_id,
        )
        return saved

    async def set_published(
        self, post_id: uuid.UUID, *, is_published: bool, actor_id: uuid.UUID
    ) -> BlogPostEntity:
        await self.get_post(post_id)  # 404s if unknown
        updated = await self._post_repo.set_published(post_id, is_published=is_published)
        verb = "published" if is_published else "unpublished"
        await self._audit_service.record(
            action=f"blog_post.{verb}", entity_type=_ENTITY_TYPE, entity_id=str(post_id),
            actor_id=actor_id,
        )
        return updated

    async def delete_post(self, post_id: uuid.UUID, *, actor_id: uuid.UUID) -> None:
        await self.get_post(post_id)  # 404s if unknown
        await self._post_repo.delete(post_id)
        await self._audit_service.record(
            action="blog_post.deleted", entity_type=_ENTITY_TYPE, entity_id=str(post_id),
            actor_id=actor_id,
        )
