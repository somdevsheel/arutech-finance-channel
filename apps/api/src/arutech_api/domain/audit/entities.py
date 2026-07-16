import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class AuditLogEntity:
    action: str
    entity_type: str
    entity_id: str
    actor_id: uuid.UUID | None = None
    extra_metadata: dict[str, Any] | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
