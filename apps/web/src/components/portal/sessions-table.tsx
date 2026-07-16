"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDateTime } from "@/lib/format";
import { logoutAllAction, revokeSessionAction } from "@/lib/auth/actions";
import type { AuthSession } from "@/types/auth";

export function SessionsTable({ sessions }: { sessions: AuthSession[] }) {
  const router = useRouter();
  const [revokingId, startRevoke] = useTransition();
  const [signingOutAll, startSignOutAll] = useTransition();

  function handleRevoke(sessionId: string) {
    startRevoke(async () => {
      const result = await revokeSessionAction(sessionId);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      toast.success("Session revoked");
      router.refresh();
    });
  }

  function handleSignOutAll() {
    startSignOutAll(async () => {
      await logoutAllAction();
      router.push("/login");
    });
  }

  if (sessions.length === 0) {
    return <p className="text-sm text-muted-foreground">No active sessions.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Device</TableHead>
              <TableHead>IP address</TableHead>
              <TableHead>Signed in</TableHead>
              <TableHead>Expires</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sessions.map((session) => (
              <TableRow key={session.id}>
                <TableCell className="max-w-56 truncate" title={session.user_agent ?? undefined}>
                  {session.user_agent ?? "Unknown device"}
                </TableCell>
                <TableCell>{session.ip_address ?? "Unknown"}</TableCell>
                <TableCell>
                  {session.created_at ? formatDateTime(session.created_at) : "Unknown"}
                </TableCell>
                <TableCell>{formatDateTime(session.expires_at)}</TableCell>
                <TableCell className="text-right">
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    disabled={revokingId}
                    onClick={() => handleRevoke(session.id)}
                  >
                    Revoke
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <Button
        type="button"
        variant="outline"
        disabled={signingOutAll}
        onClick={handleSignOutAll}
      >
        {signingOutAll ? "Signing out everywhere..." : "Sign out of all devices"}
      </Button>
    </div>
  );
}
