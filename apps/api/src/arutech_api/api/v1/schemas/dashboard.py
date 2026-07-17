from datetime import datetime

from pydantic import BaseModel

from arutech_api.domain.dashboard.entities import AlertSeverity
from arutech_api.domain.leads.entities import LeadStatus


class ExecutiveKpisResponse(BaseModel):
    total_revenue: int
    total_commission: int
    employees_count: int
    customers_count: int
    leads_total: int
    leads_conversion_rate: float
    loans_total: int
    loans_pending_approval: int
    loans_disbursed_count: int


class FunnelStageResponse(BaseModel):
    status: LeadStatus
    count: int


class LeadFunnelResponse(BaseModel):
    stages: list[FunnelStageResponse]
    disqualified_count: int
    conversion_rate: float


class HeatmapCellResponse(BaseModel):
    day_of_week: int
    hour: int
    lead_count: int
    application_count: int


class ActivityHeatmapResponse(BaseModel):
    cells: list[HeatmapCellResponse]
    generated_at: datetime


class AlertResponse(BaseModel):
    severity: AlertSeverity
    code: str
    message: str
    value: int


class SystemHealthResponse(BaseModel):
    status: str
    database_ok: bool
    redis_ok: bool
    checked_at: datetime
