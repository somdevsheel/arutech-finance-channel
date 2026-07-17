import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LoanProductEntity:
    """The database-backed replacement for the old `products.py`'s static
    `LOAN_PRODUCTS` dict — Phase 9's "Loan Product Management" /
    "Interest Rate Management" (rate bounds are just fields here, not a
    separate mechanism). `LoanApplicationService` now validates a
    requested amount/tenure/rate and seeds the document checklist from
    this, not a hardcoded module — see docs/phase-9-architecture.md for
    what's *not* migrated (the public marketing catalog stays static
    content, on purpose)."""

    slug: str
    name: str
    interest_rate_min: Decimal
    interest_rate_max: Decimal
    tenure_min_months: int
    tenure_max_months: int
    amount_min: int
    amount_max: int
    documents_required: tuple[str, ...]
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
