import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/session";
import { AdminHeader } from "@/components/admin/admin-header";

// A plain (non-route-group) `admin/` folder, not `(admin)/` — this genuinely
// needs its own URL segment (`/admin/*`), unlike `(marketing)`/`(portal)`
// which share one flat namespace on purpose. See docs/phase-8-architecture.md
// for the route-collision bug in Phase 7 this sidesteps.
//
// Role-gated to `admin` specifically, not just "authenticated": the backend's
// `dashboard.read` permission is admin-only (see seed_data.py), and
// project.md scopes "Admin Dashboard" to Phase 8, with a separate "Employee
// Portal" landing later as Phase 10. A logged-in customer or employee hitting
// `/admin/*` is redirected, not shown a 403 page — same reasoning as
// (portal)/layout.tsx re-checking auth independently of proxy.ts.
export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login?next=/admin/dashboard");
  }
  if (user.role !== "admin") {
    redirect("/dashboard");
  }

  return (
    <div className="min-h-svh bg-muted/20">
      <AdminHeader user={user} />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
