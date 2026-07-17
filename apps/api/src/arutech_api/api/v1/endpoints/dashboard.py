from typing import Annotated

from fastapi import APIRouter, Depends

from arutech_api.api.deps import get_dashboard_service, require_permission
from arutech_api.api.v1.schemas.dashboard import (
    ActivityHeatmapResponse,
    AlertResponse,
    ExecutiveKpisResponse,
    FunnelStageResponse,
    HeatmapCellResponse,
    LeadFunnelResponse,
    SystemHealthResponse,
)
from arutech_api.domain.users.entities import UserEntity
from arutech_api.services.dashboard_service import DashboardService

router = APIRouter(prefix="/admin/dashboard", tags=["dashboard"])

DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
CanReadDashboard = Annotated[UserEntity, Depends(require_permission("dashboard.read"))]


@router.get("/kpis", response_model=ExecutiveKpisResponse)
async def executive_kpis(
    _authorized: CanReadDashboard, dashboard_service: DashboardServiceDep
) -> ExecutiveKpisResponse:
    kpis = await dashboard_service.get_executive_kpis()
    return ExecutiveKpisResponse(
        total_revenue=kpis.total_revenue,
        total_commission=kpis.total_commission,
        employees_count=kpis.employees_count,
        customers_count=kpis.customers_count,
        leads_total=kpis.leads_total,
        leads_conversion_rate=kpis.leads_conversion_rate,
        loans_total=kpis.loans_total,
        loans_pending_approval=kpis.loans_pending_approval,
        loans_disbursed_count=kpis.loans_disbursed_count,
    )


@router.get("/lead-funnel", response_model=LeadFunnelResponse)
async def lead_funnel(
    _authorized: CanReadDashboard, dashboard_service: DashboardServiceDep
) -> LeadFunnelResponse:
    funnel = await dashboard_service.get_lead_funnel()
    return LeadFunnelResponse(
        stages=[
            FunnelStageResponse(status=stage.status, count=stage.count)
            for stage in funnel.stages
        ],
        disqualified_count=funnel.disqualified_count,
        conversion_rate=funnel.conversion_rate,
    )


@router.get("/activity-heatmap", response_model=ActivityHeatmapResponse)
async def activity_heatmap(
    _authorized: CanReadDashboard, dashboard_service: DashboardServiceDep
) -> ActivityHeatmapResponse:
    heatmap = await dashboard_service.get_activity_heatmap()
    return ActivityHeatmapResponse(
        cells=[
            HeatmapCellResponse(
                day_of_week=cell.day_of_week,
                hour=cell.hour,
                lead_count=cell.lead_count,
                application_count=cell.application_count,
            )
            for cell in heatmap.cells
        ],
        generated_at=heatmap.generated_at,
    )


@router.get("/alerts", response_model=list[AlertResponse])
async def alerts(
    _authorized: CanReadDashboard, dashboard_service: DashboardServiceDep
) -> list[AlertResponse]:
    items = await dashboard_service.get_alerts()
    return [
        AlertResponse(
            severity=item.severity, code=item.code, message=item.message, value=item.value
        )
        for item in items
    ]


@router.get("/system-health", response_model=SystemHealthResponse)
async def system_health(
    _authorized: CanReadDashboard, dashboard_service: DashboardServiceDep
) -> SystemHealthResponse:
    health = await dashboard_service.get_system_health()
    return SystemHealthResponse(
        status=health.status,
        database_ok=health.database_ok,
        redis_ok=health.redis_ok,
        checked_at=health.checked_at,
    )
