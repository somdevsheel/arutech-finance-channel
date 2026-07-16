import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getActiveSessions, getCurrentUser } from "@/lib/auth/session";
import { SessionsTable } from "@/components/portal/sessions-table";

export const metadata: Metadata = {
  title: "Sessions",
  robots: { index: false, follow: false },
};

export default async function SessionsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const sessions = await getActiveSessions();

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Sessions</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Devices currently signed in to your account.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Signed-in devices</CardTitle>
          <CardDescription>
            Revoke any session you don&apos;t recognize, or sign out everywhere at once.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SessionsTable sessions={sessions} />
        </CardContent>
      </Card>
    </div>
  );
}
