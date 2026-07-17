from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from arutech_api.domain.notifications.entities import NotificationChannel
from arutech_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class NotificationTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notification_templates"

    code: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(
            NotificationChannel,
            name="notification_channel",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
