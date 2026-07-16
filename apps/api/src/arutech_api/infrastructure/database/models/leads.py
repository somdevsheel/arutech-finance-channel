import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from arutech_api.domain.leads.entities import LeadSource, LeadStatus, LeadTaskStatus
from arutech_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "leads"

    contact_submission_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("contact_submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )
    source: Mapped[LeadSource] = mapped_column(
        Enum(
            LeadSource,
            name="lead_source",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=LeadSource.MANUAL,
    )
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(
            LeadStatus,
            name="lead_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=LeadStatus.NEW,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )


class LeadTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_tasks"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[LeadTaskStatus] = mapped_column(
        Enum(
            LeadTaskStatus,
            name="lead_task_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=LeadTaskStatus.PENDING,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
