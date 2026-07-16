import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class CustomerSegment(StrEnum):
    """A small, honest starter set — manually assigned by a relationship
    manager, not computed. Automated segmentation needs loan value/
    engagement data that doesn't exist until Phase 7 (LOS); revisit then
    rather than fabricating a scoring formula off data that isn't real."""

    NEW = "new"
    ACTIVE = "active"
    HIGH_VALUE = "high_value"
    AT_RISK = "at_risk"
    DORMANT = "dormant"


@dataclass(frozen=True, slots=True)
class CustomerProfileEntity:
    """CRM-specific extension of an existing `UserEntity` (role=customer).
    Deliberately doesn't duplicate name/email onto itself the way
    `LeadEntity` copies contact-submission fields (Phase 5): a
    `CustomerProfile` always extends a permanent, already-authoritative
    User record, so joining for display data avoids a second copy that
    could drift, where Lead's denormalization was decoupling from a
    submission that intentionally *shouldn't* keep changing underneath
    it. One profile per user — created lazily on first CRM interaction,
    not at registration, to keep Phase 6 from reaching back into Phase
    2's registration flow."""

    user_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    relationship_manager_id: uuid.UUID | None = None
    segment: CustomerSegment = CustomerSegment.NEW
    tags: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InteractionChannel(StrEnum):
    """Covers project.md's "Call Logs", "Email Logs", "WhatsApp Logs",
    "Meeting History", and "Follow-up Notes" as one mechanism with a
    channel discriminator, not five overlapping tables — the same
    consolidation Phase 5 applied to follow-up scheduling/tasks/
    reminders."""

    CALL = "call"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    MEETING = "meeting"
    NOTE = "note"


class InteractionDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


@dataclass(frozen=True, slots=True)
class InteractionEntity:
    """A single logged touchpoint with a customer — the atomic unit both
    "Interaction History" and "Customer Timeline" are built from."""

    customer_user_id: uuid.UUID
    channel: InteractionChannel
    summary: str
    logged_by: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    direction: InteractionDirection = InteractionDirection.OUTBOUND
    notes: str | None = None
    occurred_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CustomerAnalyticsSummary:
    total_customers: int
    by_segment: dict[CustomerSegment, int]
    customers_without_relationship_manager: int
    total_interactions: int
    by_channel: dict[InteractionChannel, int]
