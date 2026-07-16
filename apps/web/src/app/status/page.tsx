import type { Metadata } from "next";
import { SystemStatusCard } from "@/components/system-status-card";

export const metadata: Metadata = {
  title: "System Status",
  robots: { index: false, follow: false },
};

export default function StatusPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight">
          Arutech Finance Platform
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Internal operational status — not indexed, not linked from the
          public site.
        </p>
      </div>
      <SystemStatusCard />
    </main>
  );
}
