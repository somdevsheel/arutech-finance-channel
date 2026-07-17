import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LeadFunnel } from "@/types/dashboard";

const STAGE_LABELS: Record<string, string> = {
  new: "New",
  contacted: "Contacted",
  qualified: "Qualified",
  converted: "Converted",
};

export function LeadFunnelChart({ funnel }: { funnel: LeadFunnel }) {
  const maxCount = Math.max(1, ...funnel.stages.map((stage) => stage.count));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Lead Funnel</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {funnel.stages.map((stage) => (
          <div key={stage.status} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{STAGE_LABELS[stage.status] ?? stage.status}</span>
              <span className="text-muted-foreground">{stage.count}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${Math.max(4, (stage.count / maxCount) * 100)}%` }}
              />
            </div>
          </div>
        ))}
        <div className="flex items-center justify-between border-t pt-3 text-sm text-muted-foreground">
          <span>Disqualified</span>
          <span>{funnel.disqualified_count}</span>
        </div>
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Conversion rate</span>
          <span>{(funnel.conversion_rate * 100).toFixed(1)}%</span>
        </div>
      </CardContent>
    </Card>
  );
}
