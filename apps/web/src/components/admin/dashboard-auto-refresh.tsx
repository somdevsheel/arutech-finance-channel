"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const REFRESH_INTERVAL_MS = 30_000;

/**
 * project.md's "Real-Time Monitoring" — implemented as a periodic
 * `router.refresh()`, which re-runs the dashboard page's Server Component
 * fetches (session.ts, httpOnly-cookie-authenticated) on the same
 * interval `use-platform-health.ts` already polls at, rather than a
 * WebSocket/SSE push layer this project doesn't otherwise need. This
 * component renders nothing; it's mounted once on the dashboard page
 * purely for the interval side effect. See
 * docs/phase-8-architecture.md.
 */
export function DashboardAutoRefresh() {
  const router = useRouter();

  useEffect(() => {
    const id = setInterval(() => router.refresh(), REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [router]);

  return null;
}
