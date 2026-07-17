import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from arutech_api.api.deps import get_blog_post_service, require_permission
from arutech_api.api.v1.schemas.cms import (
    BlogPostCreateRequest,
    BlogPostResponse,
    BlogPostUpdateRequest,
    BlogSectionSchema,
)
from arutech_api.domain.cms.entities import BlogPostEntity, BlogSection
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.blog_post_service import BlogPostService

router = APIRouter(prefix="/cms/blog-posts", tags=["cms"])

BlogPostServiceDep = Annotated[BlogPostService, Depends(get_blog_post_service)]
CanReadCms = Annotated[UserEntity, Depends(require_permission("cms.read"))]
CanManageCms = Annotated[UserEntity, Depends(require_permission("cms.manage"))]


def _to_response(post: BlogPostEntity) -> BlogPostResponse:
    return BlogPostResponse(
        id=post.id,
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        author=post.author,
        reading_minutes=post.reading_minutes,
        sections=[
            BlogSectionSchema(heading=section.heading, paragraphs=list(section.paragraphs))
            for section in post.sections
        ],
        tags=list(post.tags),
        is_published=post.is_published,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _sections_from_schema(sections: list[BlogSectionSchema]) -> list[BlogSection]:
    return [BlogSection(heading=s.heading, paragraphs=tuple(s.paragraphs)) for s in sections]


@router.get("", response_model=list[BlogPostResponse])
async def list_blog_posts(
    _authorized: CanReadCms, service: BlogPostServiceDep, limit: int = 50, offset: int = 0
) -> list[BlogPostResponse]:
    posts = await service.list_posts(limit=limit, offset=offset)
    return [_to_response(post) for post in posts]


@router.post("", response_model=BlogPostResponse)
async def create_blog_post(
    payload: BlogPostCreateRequest, authorized: CanManageCms, service: BlogPostServiceDep
) -> BlogPostResponse:
    post = await service.create_post(
        slug=payload.slug,
        title=payload.title,
        excerpt=payload.excerpt,
        author=payload.author,
        reading_minutes=payload.reading_minutes,
        sections=_sections_from_schema(payload.sections),
        tags=payload.tags,
        actor_id=authorized.id,
    )
    return _to_response(post)


@router.get("/{post_id}", response_model=BlogPostResponse)
async def get_blog_post(
    post_id: uuid.UUID, _authorized: CanReadCms, service: BlogPostServiceDep
) -> BlogPostResponse:
    post = await service.get_post(post_id)
    return _to_response(post)


@router.put("/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: uuid.UUID,
    payload: BlogPostUpdateRequest,
    authorized: CanManageCms,
    service: BlogPostServiceDep,
) -> BlogPostResponse:
    post = await service.update_post(
        post_id,
        title=payload.title,
        excerpt=payload.excerpt,
        author=payload.author,
        reading_minutes=payload.reading_minutes,
        sections=_sections_from_schema(payload.sections),
        tags=payload.tags,
        actor_id=authorized.id,
    )
    return _to_response(post)


@router.post("/{post_id}/publish", response_model=BlogPostResponse)
async def publish_blog_post(
    post_id: uuid.UUID, authorized: CanManageCms, service: BlogPostServiceDep
) -> BlogPostResponse:
    post = await service.set_published(post_id, is_published=True, actor_id=authorized.id)
    return _to_response(post)


@router.post("/{post_id}/unpublish", response_model=BlogPostResponse)
async def unpublish_blog_post(
    post_id: uuid.UUID, authorized: CanManageCms, service: BlogPostServiceDep
) -> BlogPostResponse:
    post = await service.set_published(post_id, is_published=False, actor_id=authorized.id)
    return _to_response(post)


@router.delete("/{post_id}", status_code=204)
async def delete_blog_post(
    post_id: uuid.UUID, authorized: CanManageCms, service: BlogPostServiceDep
) -> None:
    await service.delete_post(post_id, actor_id=authorized.id)
