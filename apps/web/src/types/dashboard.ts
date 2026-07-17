export type LeadStatus = "new" | "contacted" | "qualified" | "converted" | "disqualified";
export type AlertSeverity = "info" | "warning" | "critical";

export interface ExecutiveKpis {
  total_revenue: number;
  total_commission: number;
  employees_count: number;
  customers_count: number;
  leads_total: number;
  leads_conversion_rate: number;
  loans_total: number;
  loans_pending_approval: number;
  loans_disbursed_count: number;
}

export interface FunnelStage {
  status: LeadStatus;
  count: number;
}

export interface LeadFunnel {
  stages: FunnelStage[];
  disqualified_count: number;
  conversion_rate: number;
}

export interface HeatmapCell {
  day_of_week: number; // 0 = Sunday .. 6 = Saturday
  hour: number; // 0-23
  lead_count: number;
  application_count: number;
}

export interface ActivityHeatmap {
  cells: HeatmapCell[];
  generated_at: string;
}

export interface DashboardAlert {
  severity: AlertSeverity;
  code: string;
  message: string;
  value: number;
}

export interface SystemHealth {
  status: string;
  database_ok: boolean;
  redis_ok: boolean;
  checked_at: string;
}
