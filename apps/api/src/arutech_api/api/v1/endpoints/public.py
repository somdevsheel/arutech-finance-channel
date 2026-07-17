from typing import Annotated

from fastapi import APIRouter, Depends, Request

from arutech_api.api.deps import get_blog_post_service, get_contact_service
from arutech_api.api.v1.schemas.cms import BlogPostResponse, BlogSectionSchema
from arutech_api.api.v1.schemas.common import MessageResponse
from arutech_api.api.v1.schemas.public import ContactRequest
from arutech_api.core.rate_limit import limiter
from arutech_api.domain.cms.entities import BlogPostEntity
from arutech_api.services.blog_post_service import BlogPostService
from arutech_api.services.contact_service import ContactService

router = APIRouter(prefix="/public", tags=["public"])

ContactServiceDep = Annotated[ContactService, Depends(get_contact_service)]
BlogPostServiceDep = Annotated[BlogPostService, Depends(get_blog_post_service)]


def _blog_post_response(post: BlogPostEntity) -> BlogPostResponse:
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


@router.post("/contact", response_model=MessageResponse)
@limiter.limit("5/minute")
async def submit_contact_form(
    request: Request, payload: ContactRequest, contact_service: ContactServiceDep
) -> MessageResponse:
    await contact_service.submit(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        subject=payload.subject,
        message=payload.message,
        honeypot=payload.website,
    )
    return MessageResponse(message="Thanks for reaching out — we'll get back to you soon.")


@router.get("/blog-posts", response_model=list[BlogPostResponse])
async def list_published_blog_posts(
    blog_service: BlogPostServiceDep, limit: int = 50, offset: int = 0
) -> list[BlogPostResponse]:
    posts = await blog_service.list_published_posts(limit=limit, offset=offset)
    return [_blog_post_response(post) for post in posts]


@router.get("/blog-posts/{slug}", response_model=BlogPostResponse)
async def get_published_blog_post(slug: str, blog_service: BlogPostServiceDep) -> BlogPostResponse:
    post = await blog_service.get_published_post(slug)
    return _blog_post_response(post)
