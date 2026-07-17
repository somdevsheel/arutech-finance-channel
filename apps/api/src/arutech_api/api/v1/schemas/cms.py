import uuid
from datetime import datetime

from pydantic import BaseModel


class BlogSectionSchema(BaseModel):
    heading: str | None = None
    paragraphs: list[str]


class BlogPostResponse(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    excerpt: str
    author: str
    reading_minutes: int
    sections: list[BlogSectionSchema]
    tags: list[str]
    is_published: bool
    published_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class BlogPostCreateRequest(BaseModel):
    slug: str
    title: str
    excerpt: str
    author: str
    reading_minutes: int
    sections: list[BlogSectionSchema] = []
    tags: list[str] = []


class BlogPostUpdateRequest(BaseModel):
    title: str
    excerpt: str
    author: str
    reading_minutes: int
    sections: list[BlogSectionSchema] = []
    tags: list[str] = []
