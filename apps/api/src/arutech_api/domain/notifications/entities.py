import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class NotificationChannel(StrEnum):
    """project.md lists "Email Templates", "SMS Templates", and "WhatsApp
    Templates" as three items; they're the same shape of record (a code,
    a body with placeholders, an active flag), so this is one entity with
    a channel discriminator — the same consolidation this project has
    applied to every other "N similar things" list in project.md (CRM's
    interaction channels, this phase's Bank/NBFC -> Lender)."""

    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


@dataclass(frozen=True, slots=True)
class NotificationTemplateEntity:
    """A template's *content*, not a send. Nothing in this codebase
    renders or delivers these yet — `OtpDeliveryPort` (Phase 2) still
    just logs a code via `LoggingOtpDeliveryChannel`. Real
    rendering/delivery across email/SMS/WhatsApp providers is Phase 13's
    "Notification Center"; this phase only lets an admin author and
    manage the content that phase will eventually render, the same
    forward-looking-but-honest split Phase 2's port/adapter established.
    `body` uses `{{variable}}` placeholders — a convention, not something
    any code parses yet."""

    code: str  # stable key, e.g. "loan.approved", "otp.login"
    channel: NotificationChannel
    body: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    subject: str | None = None  # email only
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
