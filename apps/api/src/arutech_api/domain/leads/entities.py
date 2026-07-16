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
    an audit trail is supposed to be recording faithfully.
    """

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    DISQUALIFIED = "disqualified"


ALLOWED_TRANSITIONS: dict[LeadStatus, frozenset[LeadStatus]] = {
    LeadStatus.NEW: frozenset({LeadStatus.CONTACTED, LeadStatus.DISQUALIFIED}),
    LeadStatus.CONTACTED: frozenset({LeadStatus.QUALIFIED, LeadStatus.DISQUALIFIED}),
    LeadStatus.QUALIFIED: frozenset({LeadStatus.CONVERTED, LeadStatus.DISQUALIFIED}),
    LeadStatus.CONVERTED: frozenset(),
    LeadStatus.DISQUALIFIED: frozenset(),
}


def is_transition_allowed(current: LeadStatus, target: LeadStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


@dataclass(frozen=True, slots=True)
class LeadEntity:
    """A sales lead. Currently always created from a `ContactSubmissionEntity`
    (see `LeadService.create_from_contact_submission`) — `contact_submission_id`
    keeps that provenance, while name/email/phone are copied onto the lead
    itself (not joined at read time) since a lead's contact details can be
    corrected by an employee independently of the original submission."""

    contact_submission_id: uuid.UUID
    name: str
    email: str
    phone: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: LeadStatus = LeadStatus.NEW
    score: int = 0
    assigned_to: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
