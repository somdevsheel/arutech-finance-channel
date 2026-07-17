import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BlogSection:
    """Mirrors `apps/web/src/content/blog-posts.ts`'s `BlogSection` shape
    exactly, so migrating the 3 existing posts into the database is a
    literal data copy, not a reshaping."""

    paragraphs: tuple[str, ...]
    heading: str | None = None


@dataclass(frozen=True, slots=True)
class BlogPostEntity:
    """project.md's "CMS" — scoped to blog posts specifically (see
    docs/phase-9-architecture.md for why FAQs/job-openings/nav-links stay
    static). `is_published` + `published_at` let a post exist as a draft
    before it's public; the public `/api/v1/public/blog-posts*` routes
    only ever return published posts, the same dual-access pattern
    Phase 7 established for loan applications (customer-facing vs.
    staff-facing) applied here to (visitor-facing vs. editor-facing)."""

    slug: str
    title: str
    excerpt: str
    author: str
    reading_minutes: int
    sections: tuple[BlogSection, ...]
    tags: tuple[str, ...] = ()
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    is_published: bool = False
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
