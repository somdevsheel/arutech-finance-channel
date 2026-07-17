from decimal import Decimal

from sqlalchemy import JSON, Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from arutech_api.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LoanProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "loan_products"

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    interest_rate_min: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    interest_rate_max: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    tenure_min_months: Mapped[int] = mapped_column(Integer)
    tenure_max_months: Mapped[int] = mapped_column(Integer)
    amount_min: Mapped[int] = mapped_column(Integer)
    amount_max: Mapped[int] = mapped_column(Integer)
    # JSON (not JSONB), matching Phase 8's EXTRACT(DOW) lesson: the
    # generic type works identically on Postgres and the SQLite test DB.
    documents_required: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
