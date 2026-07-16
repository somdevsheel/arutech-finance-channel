import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { FileText, KeyRound, UserRound } from "lucide-react";
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getActiveSessions, getCurrentUser } from "@/lib/auth/session";

export const metadata: Metadata = {
  title: "Dashboard",
  robots: { index: false, follow: false },
};

export default async function DashboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const sessions = await getActiveSessions();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Welcome back, {user.full_name.split(" ")[0]}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Here&apos;s an overview of your Arutech Finance account.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileText className="size-4 text-muted-foreground" />
              <CardTitle>Loan applications</CardTitle>
            </div>
            <CardDescription>
              You don&apos;t have any applications yet. Applying online arrives in a later
              phase of the platform.
            </CardDescription>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <UserRound className="size-4 text-muted-foreground" />
              <CardTitle>Profile</CardTitle>
            </div>
            <CardDescription>
              {user.is_verified ? "Your account is verified." : "Your account isn't verified yet."}
            </CardDescription>
            <CardAction>
              <Button size="sm" variant="outline" render={<Link href="/profile" />}>
                View
              </Button>
            </CardAction>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <KeyRound className="size-4 text-muted-foreground" />
              <CardTitle>Active sessions</CardTitle>
            </div>
            <CardDescription>
              {sessions.length} signed-in {sessions.length === 1 ? "device" : "devices"}.
            </CardDescription>
            <CardAction>
              <Button size="sm" variant="outline" render={<Link href="/sessions" />}>
                Manage
              </Button>
            </CardAction>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
