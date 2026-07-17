from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from arutech_api.domain.leads.entities import LeadStatus


@dataclass(frozen=True, slots=True)
class ExecutiveKpis:
    """project.md's "Business KPIs" (Revenue, Commission, Employees,
    Customers, Loans, Approvals) in one read-model. Revenue is the total
    disbursed loan volume this DSA has facilitated (business volume, not
    the lender's interest income); Commission is what the DSA actually
    earns from it — two different numbers project.md deliberately lists
    separately. Both are already tracked per-application by Phase 7, so
    this is a sum, not a new computation."""

    total_revenue: int
    total_commission: int
    employees_count: int
    customers_count: int
    leads_total: int
    leads_conversion_rate: float
    loans_total: int
    loans_pending_approval: int
    loans_disbursed_count: int


@dataclass(frozen=True, slots=True)
class FunnelStageEntry:
    status: LeadStatus
    count: int


@dataclass(frozen=True, slots=True)
class LeadFunnel:
    """project.md's "Lead Funnel" / "Conversion" analytics. Deliberately a
    *current-status* distribution in pipeline order, not a historical
    cohort funnel (e.g. "of leads created in January, how many ever
    reached QUALIFIED") — that needs stage-transition timestamps as a
    dedicated fact table, which doesn't exist; `AuditLog` records
    transitions but reconstructing cohort funnels from its free-form
    metadata would be fragile. `stages` covers the four pipeline statuses
    in order (NEW -> CONTACTED -> QUALIFIED -> CONVERTED);
    `disqualified_count` is reported alongside, not as a funnel stage,
    since a disqualified lead has left the pipeline rather than
    progressed through it."""

    stages: tuple[FunnelStageEntry, ...]
    disqualified_count: int
    conversion_rate: float


@dataclass(frozen=True, slots=True)
class HeatmapCell:
    day_of_week: int  # 0 = Sunday .. 6 = Saturday (SQL EXTRACT(DOW) convention)
    hour: int  # 0-23, server-local time (see ActivityHeatmap docstring)
    lead_count: int
    application_count: int


@dataclass(frozen=True, slots=True)
class ActivityHeatmap:
    """project.md's "Heatmaps". A temporal (day-of-week x hour-of-day)
    activity grid built from `leads.created_at` and
    `loan_applications.created_at` — the only timestamp data that exists
    for this. A *geographic* heatmap was considered and dropped: neither
    `LeadEntity` nor `CustomerProfileEntity` nor `UserEntity` has a
    city/state/region field anywhere in the system, so a geo heatmap
    would mean inventing location data that isn't collected, not
    visualizing something real. `cells` is always a dense 7x24 = 168-cell
    grid (zero-filled for empty buckets) so the frontend never needs to
    handle missing keys."""

    cells: tuple[HeatmapCell, ...]
    generated_at: datetime


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Alert:
    """project.md's "Alerts", under Real-Time Monitoring. A small,
    deterministic set of threshold checks over data that already exists
    (see `dashboard/alerts.py`) — not a configurable alerting/notification
    system with delivery channels, which is Phase 13's "Notification
    Center" territory. `code` is a stable machine-readable identifier so
    a future notification integration has something to key off; `message`
    is the human-readable form the dashboard renders directly."""

    severity: AlertSeverity
    code: str
    message: str
    value: int


@dataclass(frozen=True, slots=True)
class SystemHealthSummary:
    """Wraps the same liveness checks `/health/ready` already performs
    (Phase 1) for the admin dashboard, rather than standing up a second,
    parallel health-check mechanism. "Real-Time Monitoring" here means the
    dashboard polls this on an interval (see the frontend's auto-refresh,
    documented in docs/phase-8-architecture.md) — there's no WebSocket/SSE
    push layer, which would be infrastructure this project doesn't
    otherwise need."""

    status: str  # "ok" | "degraded"
    database_ok: bool
    redis_ok: bool
    checked_at: datetime
