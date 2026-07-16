import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ContactSubmissionEntity:
    name: str
    email: str
    subject: str
    message: str
    phone: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
