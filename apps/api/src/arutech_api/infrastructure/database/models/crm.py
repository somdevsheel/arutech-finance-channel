import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Table,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arutech_api.domain.crm.entities import (
    CustomerSegment,
    InteractionChannel,
    InteractionDirection,
)
from arutech_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

customer_tags = Table(
    "customer_tags",
    Base.metadata,
    Column(
        "customer_profile_id",
        Uuid(as_uuid=True),
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", Uuid(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Tag(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)


class CustomerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    relationship_manager_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    segment: Mapped[CustomerSegment] = mapped_column(
        Enum(
            CustomerSegment,
            name="customer_segment",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=CustomerSegment.NEW,
        index=True,
    )

    tags: Mapped[list[Tag]] = relationship(secondary=customer_tags, lazy="selectin")


class Interaction(UUIDPrimaryKeyMixin, Base):
    # No TimestampMixin: like contact_submissions, this is append-only — an
    # interaction log entry is never edited after creation, so `updated_at`
    # would never actually change. `occurred_at` (when the call/meeting/
    # email actually happened) is a separate, always-explicit domain
    # concept from `created_at` (when it was logged into the system).
    __tablename__ = "interactions"

    customer_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[InteractionChannel] = mapped_column(
        Enum(
            InteractionChannel,
            name="interaction_channel",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        index=True,
    )
    direction: Mapped[InteractionDirection] = mapped_column(
        Enum(
            InteractionDirection,
            name="interaction_direction",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=InteractionDirection.OUTBOUND,
    )
    summary: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    logged_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
