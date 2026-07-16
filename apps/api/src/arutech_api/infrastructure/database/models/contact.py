from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from arutech_api.infrastructure.database.base import Base, UUIDPrimaryKeyMixin

# No TimestampMixin: like refresh_tokens/otp_codes, this is append-only —
# a submission is never updated after creation, so `updated_at` would never
# actually change.


class ContactSubmission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "contact_submissions"

    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    subject: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
