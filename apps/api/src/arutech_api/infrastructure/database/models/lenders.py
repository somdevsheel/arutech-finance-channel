from decimal import Decimal

from sqlalchemy import Boolean, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from arutech_api.domain.lenders.entities import LenderType
from arutech_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Lender(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lenders"

    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[LenderType] = mapped_column(
        Enum(
            LenderType,
            name="lender_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    commission_rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
