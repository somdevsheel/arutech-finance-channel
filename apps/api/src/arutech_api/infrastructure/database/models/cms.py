from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from arutech_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BlogPost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "blog_posts"

    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    excerpt: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(255))
    reading_minutes: Mapped[int] = mapped_column(Integer)
    # A list of {"heading": str | None, "paragraphs": [str, ...]} objects —
    # JSON (not JSONB), same cross-dialect reasoning as loan_products'
    # documents_required.
    sections: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
