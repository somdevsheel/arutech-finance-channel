import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata: Metadata = {
  title: "Profile",
  robots: { index: false, follow: false },
};

const ROLE_LABELS: Record<string, string> = {
  customer: "Customer",
  employee: "Employee",
  partner: "Partner",
  admin: "Administrator",
};

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b py-3 text-sm last:border-b-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

export default async function ProfilePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="mt-1 text-sm text-muted-foreground">Your account details.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>
            Editing these details arrives with account settings in a later phase.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Field label="Full name" value={user.full_name} />
          <Field label="Email" value={user.email} />
          <Field label="Phone" value={user.phone ?? "Not set"} />
          <Field label="Account type" value={ROLE_LABELS[user.role] ?? user.role} />
          <Field
            label="Verification"
            value={
              <Badge variant={user.is_verified ? "default" : "secondary"}>
                {user.is_verified ? "Verified" : "Not verified"}
              </Badge>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}
