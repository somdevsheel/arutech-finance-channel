import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class LenderType(StrEnum):
    """project.md lists "Bank Management" and "NBFC Management" as two
    separate items; they're the same shape of record (an institution this
    DSA routes applications to and earns commission from), so this is one
    entity with a type discriminator, not two tables — the same
    consolidation Phase 6 applied to interaction channels and Phase 5 to
    follow-up scheduling."""

    BANK = "bank"
    NBFC = "nbfc"


@dataclass(frozen=True, slots=True)
class LenderEntity:
    """The catalog entry Phase 7's `assigned_to` (an employee) stood in
    for real "Bank Routing" — see that phase's "Honest simplifications".
    Routing applications to a specific lender is still a later phase's
    work (needs a Partner Bank Portal, Phase 11, to mean anything); this
    phase only builds the catalog and the commission rate it carries,
    satisfying "Commission Management" without inventing per-partner
    rate history no one asked for yet."""

    name: str
    type: LenderType
    code: str  # short, unique — e.g. "HDFC", "BAJAJ-FIN"
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    contact_email: str | None = None
    contact_phone: str | None = None
    commission_rate_percent: Decimal = Decimal("1")
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
