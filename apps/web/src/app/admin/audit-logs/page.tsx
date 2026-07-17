import type { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDateTime } from "@/lib/format";
import { getAuditLogs } from "@/lib/admin/session";

export const metadata: Metadata = {
  title: "Audit Logs",
  robots: { index: false, follow: false },
};

export default async function AdminAuditLogsPage() {
  const entries = await getAuditLogs();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Audit Logs</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Every mutation across the platform, who did it, and when — built in Phase 2, this is
          the first admin page to surface it.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>When</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Entity</TableHead>
                  <TableHead>Actor</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="text-muted-foreground">
                      {formatDateTime(entry.created_at)}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{entry.action}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {entry.entity_type}/{entry.entity_id.slice(0, 8)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {entry.actor_id ? entry.actor_id.slice(0, 8) : "system"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
