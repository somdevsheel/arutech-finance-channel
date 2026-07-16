import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/session";
import { PortalHeader } from "@/components/portal/portal-header";

// proxy.ts already gates these routes and keeps the access cookie fresh,
// but Next's own guidance is not to rely on Proxy alone for auth (a
// matcher typo would silently remove coverage) — so this re-checks
// independently. See docs/phase-4-architecture.md.
export default async function PortalLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  return (
    <div className="min-h-svh bg-muted/20">
      <PortalHeader user={user} />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
