import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class SettingValueType(StrEnum):
    STRING = "string"
    BOOLEAN = "boolean"
    NUMBER = "number"


_TRUE_VALUES = frozenset({"true", "1", "yes"})


def parse_bool_setting(value: str) -> bool:
    """The one place a boolean-typed setting's string value is
    interpreted — both `SettingsService.get_bool` and `LeadService`
    (which depends on `SystemSettingRepository` directly, not
    `SettingsService`, to avoid a service-to-service dependency; see
    Phase 8's `DashboardService` docstring for the same reasoning) call
    this instead of duplicating the parsing."""
    return value.strip().lower() in _TRUE_VALUES


@dataclass(frozen=True, slots=True)
class SystemSettingEntity:
    """project.md's "Settings", "Feature Flags", and "Workflow
    Management" — one typed key-value store, not three mechanisms. A
    feature flag is just a boolean-typed setting; a "workflow" toggle
    (e.g. whether lead auto-assignment runs) is just a setting a service
    reads before acting — see `LeadService._auto_assign`'s use of
    `leads.auto_assignment_enabled`, the one real, wired consumer this
    phase ships rather than building a rules engine no code actually
    calls. `value` is always stored as a string; `value_type` tells a
    caller how to parse it (see `SettingsService`'s typed getters) —
    simpler than a column-per-type table for a handful of settings."""

    key: str
    value: str
    value_type: SettingValueType
    description: str = ""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    updated_at: datetime | None = None
