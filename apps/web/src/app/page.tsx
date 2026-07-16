import { SystemStatusCard } from "@/components/system-status-card";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight">
          Arutech Finance Platform
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Phase 1 foundation — public site, portals, and dashboards land in
          later phases.
        </p>
      </div>
      <SystemStatusCard />
    </main>
  );
}
