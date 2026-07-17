import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/format";
import type { SystemHealth } from "@/types/dashboard";

function StatusRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span>{label}</span>
      <Badge variant={ok ? "secondary" : "destructive"}>{ok ? "OK" : "Down"}</Badge>
    </div>
  );
}

export function SystemHealthPanel({ health }: { health: SystemHealth }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>System Health</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <StatusRow label="Database" ok={health.database_ok} />
        <StatusRow label="Redis" ok={health.redis_ok} />
        <p className="pt-2 text-xs text-muted-foreground">
          Checked {formatDateTime(health.checked_at)}
        </p>
      </CardContent>
    </Card>
  );
}
