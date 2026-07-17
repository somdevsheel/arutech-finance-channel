import type { Metadata } from "next";
import {
  getActivityHeatmap,
  getAlerts,
  getExecutiveKpis,
  getLeadFunnel,
  getSystemHealth,
} from "@/lib/admin/session";
import { ActivityHeatmap } from "@/components/admin/activity-heatmap";
import { AlertsPanel } from "@/components/admin/alerts-panel";
import { DashboardAutoRefresh } from "@/components/admin/dashboard-auto-refresh";
import { KpiCard } from "@/components/admin/kpi-card";
import { LeadFunnelChart } from "@/components/admin/lead-funnel-chart";
import { SystemHealthPanel } from "@/components/admin/system-health-panel";
import { formatInr } from "@/lib/format";

export const metadata: Metadata = {
  title: "Admin Dashboard",
  robots: { index: false, follow: false },
};

export default async function AdminDashboardPage() {
  const [kpis, funnel, heatmap, alerts, health] = await Promise.all([
    getExecutiveKpis(),
    getLeadFunnel(),
    getActivityHeatmap(),
    getAlerts(),
    getSystemHealth(),
  ]);

  return (
    <div className="space-y-8">
      <DashboardAutoRefresh />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Executive Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Business KPIs, pipeline health, and system status.
        </p>
      </div>

      {kpis && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard label="Revenue (disbursed)" value={formatInr(kpis.total_revenue)} />
          <KpiCard label="Commission" value={formatInr(kpis.total_commission)} />
          <KpiCard label="Employees" value={String(kpis.employees_count)} />
          <KpiCard label="Customers" value={String(kpis.customers_count)} />
          <KpiCard
            label="Leads"
            value={String(kpis.leads_total)}
            hint={`${(kpis.leads_conversion_rate * 100).toFixed(1)}% conversion`}
          />
          <KpiCard label="Loan Applications" value={String(kpis.loans_total)} />
          <KpiCard label="Pending Approval" value={String(kpis.loans_pending_approval)} />
          <KpiCard label="Disbursed" value={String(kpis.loans_disbursed_count)} />
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {funnel && <LeadFunnelChart funnel={funnel} />}
        {health && <SystemHealthPanel health={health} />}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {heatmap && <ActivityHeatmap heatmap={heatmap} />}
        <AlertsPanel alerts={alerts} />
      </div>
    </div>
  );
}
