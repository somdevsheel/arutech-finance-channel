import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arutech_api.core.exceptions import NotFoundError
from arutech_api.domain.cms.entities import BlogPostEntity, BlogSection
from arutech_api.domain.cms.repository import BlogPostRepository
from arutech_api.infrastructure.database.models.cms import BlogPost


def _sections_to_json(sections: tuple[BlogSection, ...]) -> list[dict[str, object]]:
    return [
        {"heading": section.heading, "paragraphs": list(section.paragraphs)}
        for section in sections
    ]


def _sections_from_json(raw: list[dict[str, object]]) -> tuple[BlogSection, ...]:
    return tuple(
        BlogSection(
            heading=section.get("heading"),  # type: ignore[arg-type]
            paragraphs=tuple(section.get("paragraphs", [])),  # type: ignore[arg-type]
        )
        for section in raw
    )


def _to_entity(model: BlogPost) -> BlogPostEntity:
    return BlogPostEntity(
        id=model.id,
        slug=model.slug,
        title=model.title,
        excerpt=model.excerpt,
        author=model.author,
        reading_minutes=model.reading_minutes,
        sections=_sections_from_json(model.sections),
        tags=tuple(model.tags),
        is_published=model.is_published,
        published_at=model.published_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyBlogPostRepository(BlogPostRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, post: BlogPostEntity) -> BlogPostEntity:
        model = BlogPost(
            id=post.id,
            slug=post.slug,
            title=post.title,
            excerpt=post.excerpt,
            author=post.author,
            reading_minutes=post.reading_minutes,
            sections=_sections_to_json(post.sections),
            tags=list(post.tags),
            is_published=post.is_published,
            published_at=post.published_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, post_id: uuid.UUID) -> BlogPostEntity | None:
        model = await self._session.get(BlogPost, post_id)
        return _to_entity(model) if model else None

    async def get_by_slug(
        self, slug: str, *, published_only: bool = False
    ) -> BlogPostEntity | None:
        query = select(BlogPost).where(BlogPost.slug == slug)
        if published_only:
            query = query.where(BlogPost.is_published.is_(True))
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_posts(
        self, *, published_only: bool = False, limit: int = 50, offset: int = 0
    ) -> list[BlogPostEntity]:
        query = select(BlogPost)
        if published_only:
            query = query.where(BlogPost.is_published.is_(True))
        query = query.order_by(
            BlogPost.published_at.desc().nulls_last(), BlogPost.created_at.desc()
        )
        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def update(self, post: BlogPostEntity) -> BlogPostEntity:
        model = await self._session.get(BlogPost, post.id)
        if model is None:
            raise NotFoundError(f"Blog post {post.id} not found")

        model.title = post.title
        model.excerpt = post.excerpt
        model.author = post.author
        model.reading_minutes = post.reading_minutes
        model.sections = _sections_to_json(post.sections)
        model.tags = list(post.tags)

        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def set_published(self, post_id: uuid.UUID, *, is_published: bool) -> BlogPostEntity:
        model = await self._session.get(BlogPost, post_id)
        if model is None:
            raise NotFoundError(f"Blog post {post_id} not found")
        model.is_published = is_published
        model.published_at = datetime.now(UTC) if is_published else None
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, post_id: uuid.UUID) -> None:
        model = await self._session.get(BlogPost, post_id)
        if model is None:
            raise NotFoundError(f"Blog post {post_id} not found")
        await self._session.delete(model)
        await self._session.flush()
