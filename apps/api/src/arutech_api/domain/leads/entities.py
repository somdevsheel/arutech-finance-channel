import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class LeadStatus(StrEnum):
    """A lead's position in the sales pipeline.

    NEW and CONTACTED/QUALIFIED can be disqualified; CONVERTED and
    DISQUALIFIED are terminal — see `ALLOWED_TRANSITIONS`. There is
    deliberately no "reopen" transition out of either terminal state: a
    disqualified or converted lead that needs revisiting is a new lead
    (or, once LOS exists, a new application), not a mutation of history
    an audit trail is supposed to be recording faithfully. A resubmission
    against a still-open (non-terminal) lead is instead treated as a
    duplicate — see `LeadService.create_from_contact_submission`.
    """

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    DISQUALIFIED = "disqualified"


TERMINAL_STATUSES = frozenset({LeadStatus.CONVERTED, LeadStatus.DISQUALIFIED})

ALLOWED_TRANSITIONS: dict[LeadStatus, frozenset[LeadStatus]] = {
    LeadStatus.NEW: frozenset({LeadStatus.CONTACTED, LeadStatus.DISQUALIFIED}),
    LeadStatus.CONTACTED: frozenset({LeadStatus.QUALIFIED, LeadStatus.DISQUALIFIED}),
    LeadStatus.QUALIFIED: frozenset({LeadStatus.CONVERTED, LeadStatus.DISQUALIFIED}),
    LeadStatus.CONVERTED: frozenset(),
    LeadStatus.DISQUALIFIED: frozenset(),
}


def is_transition_allowed(current: LeadStatus, target: LeadStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


class LeadSource(StrEnum):
    """Where a lead came from. Only two real intake mechanisms exist right
    now — the public contact form, and an employee/admin creating or bulk
    -importing one directly. LOS applications (Phase 7) will be a third
    real source when that phase lands; not modeled yet on principle (see
    Phase 2's seed_data.py comment: nothing invented for features that
    don't exist)."""

    CONTACT_FORM = "contact_form"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class LeadEntity:
    """A sales lead. `contact_submission_id` is set when `source` is
    CONTACT_FORM and null for MANUAL (directly created or imported) leads
    — a manually-entered lead never filled out the public contact form, so
    pointing it at a fabricated submission row would misrepresent history.
    name/email/phone are copied onto the lead itself (not joined at read
    time) since a lead's contact details can be corrected by an employee
    independently of the original submission."""

    name: str
    email: str
    phone: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    contact_submission_id: uuid.UUID | None = None
    source: LeadSource = LeadSource.MANUAL
    status: LeadStatus = LeadStatus.NEW
    score: int = 0
    assigned_to: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LeadAnalyticsSummary:
    """Aggregate pipeline stats — project.md's "Lead Analytics". Computed
    at read time from the leads table rather than maintained incrementally;
    revisit only if this ever shows up as a real hot path."""

    total_leads: int
    by_status: dict[LeadStatus, int]
    by_source: dict[LeadSource, int]
    average_score: float
    conversion_rate: float


class LeadTaskStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class LeadTaskEntity:
    """A scheduled follow-up on a lead — covers project.md's "Follow-up
    Scheduling", "Tasks", and "Reminders" as one mechanism rather than
    three overlapping ones: a reminder *is* a task with a due date, and a
    scheduled follow-up *is* a task assigned to whoever owns the lead."""

    lead_id: uuid.UUID
    title: str
    due_at: datetime
    assigned_to: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    notes: str | None = None
    status: LeadTaskStatus = LeadTaskStatus.PENDING
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
