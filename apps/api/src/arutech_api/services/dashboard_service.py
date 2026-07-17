from datetime import UTC, datetime

from arutech_api.core.database import check_database_connection
from arutech_api.core.redis import check_redis_connection
from arutech_api.domain.crm.repository import CustomerRepository
from arutech_api.domain.dashboard.alerts import evaluate_alerts
from arutech_api.domain.dashboard.entities import (
    ActivityHeatmap,
    Alert,
    ExecutiveKpis,
    FunnelStageEntry,
    HeatmapCell,
    LeadFunnel,
    SystemHealthSummary,
)
from arutech_api.domain.leads.entities import LeadStatus
from arutech_api.domain.leads.repository import LeadRepository
from arutech_api.domain.loans.entities import LoanApplicationStatus
from arutech_api.domain.loans.repository import LoanApplicationRepository
from arutech_api.domain.users.entities import UserRole
from arutech_api.domain.users.repository import UserRepository

# Pipeline order for the funnel view — mirrors LeadStatus's own progression
# (see domain/leads/entities.py's ALLOWED_TRANSITIONS), excluding the
# DISQUALIFIED terminal status, which LeadFunnel reports separately.
_FUNNEL_STAGES = (
    LeadStatus.NEW,
    LeadStatus.CONTACTED,
    LeadStatus.QUALIFIED,
    LeadStatus.CONVERTED,
)

# "Pending approval" means awaiting an approve/reject decision, which
# covers both SUBMITTED (not yet picked up) and UNDER_REVIEW (assigned,
# being worked) — not just UNDER_REVIEW alone, since an unassigned
# application is still waiting on staff, arguably more urgently.
_PENDING_APPROVAL_STATUSES = (
    LoanApplicationStatus.SUBMITTED,
    LoanApplicationStatus.UNDER_REVIEW,
)


def _pending_approval_count(by_status: dict[LoanApplicationStatus, int]) -> int:
    return sum(by_status.get(status, 0) for status in _PENDING_APPROVAL_STATUSES)


class DashboardService:
    """project.md's Phase 8 "Admin Dashboard" — a read-only aggregation
    layer over Lead/Customer/LoanApplication/User data that already
    exists from Phases 5-7. Deliberately depends on those repositories
    directly rather than on LeadService/CustomerService/
    LoanApplicationService: this is pure composition of read queries, not
    an orchestrator of business transactions, so there's nothing those
    services' write-side logic would add — see docs/phase-8-architecture.md.
    """

    def __init__(
        self,
        lead_repo: LeadRepository,
        customer_repo: CustomerRepository,
        loan_repo: LoanApplicationRepository,
        user_repo: UserRepository,
    ):
        self._lead_repo = lead_repo
        self._customer_repo = customer_repo
        self._loan_repo = loan_repo
        self._user_repo = user_repo

    async def get_executive_kpis(self) -> ExecutiveKpis:
        lead_summary = await self._lead_repo.get_analytics_summary()
        loan_summary = await self._loan_repo.get_analytics_summary()
        customers_total = await self._customer_repo.count_total()
        employees_count = await self._user_repo.count_by_role(UserRole.EMPLOYEE)

        return ExecutiveKpis(
            total_revenue=loan_summary.total_disbursed_amount,
            total_commission=loan_summary.total_commission_amount,
            employees_count=employees_count,
            customers_count=customers_total,
            leads_total=lead_summary.total_leads,
            leads_conversion_rate=lead_summary.conversion_rate,
            loans_total=loan_summary.total_applications,
            loans_pending_approval=_pending_approval_count(loan_summary.by_status),
            loans_disbursed_count=loan_summary.by_status.get(
                LoanApplicationStatus.DISBURSED, 0
            ),
        )

    async def get_lead_funnel(self) -> LeadFunnel:
        summary = await self._lead_repo.get_analytics_summary()
        stages = tuple(
            FunnelStageEntry(status=status, count=summary.by_status.get(status, 0))
            for status in _FUNNEL_STAGES
        )
        return LeadFunnel(
            stages=stages,
            disqualified_count=summary.by_status.get(LeadStatus.DISQUALIFIED, 0),
            conversion_rate=summary.conversion_rate,
        )

    async def get_activity_heatmap(self) -> ActivityHeatmap:
        lead_counts = await self._lead_repo.get_hourly_activity_counts()
        application_counts = await self._loan_repo.get_hourly_activity_counts()

        cells = tuple(
            HeatmapCell(
                day_of_week=day,
                hour=hour,
                lead_count=lead_counts.get((day, hour), 0),
                application_count=application_counts.get((day, hour), 0),
            )
            for day in range(7)
            for hour in range(24)
        )
        return ActivityHeatmap(cells=cells, generated_at=datetime.now(UTC))

    async def get_alerts(self) -> list[Alert]:
        lead_summary = await self._lead_repo.get_analytics_summary()
        loan_summary = await self._loan_repo.get_analytics_summary()
        unassigned_customers = await self._customer_repo.count_without_relationship_manager()

        return evaluate_alerts(
            loans_pending_approval=_pending_approval_count(loan_summary.by_status),
            customers_without_relationship_manager=unassigned_customers,
            leads_new_count=lead_summary.by_status.get(LeadStatus.NEW, 0),
            leads_total=lead_summary.total_leads,
        )

    async def get_system_health(self) -> SystemHealthSummary:
        database_ok = await check_database_connection()
        redis_ok = await check_redis_connection()
        return SystemHealthSummary(
            status="ok" if (database_ok and redis_ok) else "degraded",
            database_ok=database_ok,
            redis_ok=redis_ok,
            checked_at=datetime.now(UTC),
        )
