from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from arutech_api.domain.settings.entities import SettingValueType
from arutech_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    value_type: Mapped[SettingValueType] = mapped_column(
        Enum(
            SettingValueType,
            name="setting_value_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    description: Mapped[str] = mapped_column(String(255), default="")
