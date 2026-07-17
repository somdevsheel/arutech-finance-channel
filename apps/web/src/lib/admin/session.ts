import { apiFetch, ApiError } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth/session";
import type {
  ActivityHeatmap,
  DashboardAlert,
  ExecutiveKpis,
  LeadFunnel,
  SystemHealth,
} from "@/types/dashboard";

// Same read-only-by-design rationale as lib/auth/session.ts and
// lib/loans/session.ts: Server Components can't set cookies, and
// proxy.ts already guarantees a fresh access token before any portal
// (including admin) route runs. 401/403 both fold to an empty result —
// (admin)/layout.tsx is the real gate (see its docstring); these are a
// defensive second line, not the primary check.

function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.status === 403);
}

export async function getExecutiveKpis(): Promise<ExecutiveKpis | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) return null;

  try {
    return await apiFetch<ExecutiveKpis>("/api/v1/admin/dashboard/kpis", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (error) {
    if (isUnauthorized(error)) return null;
    throw error;
  }
}

export async function getLeadFunnel(): Promise<LeadFunnel | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) return null;

  try {
    return await apiFetch<LeadFunnel>("/api/v1/admin/dashboard/lead-funnel", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (error) {
    if (isUnauthorized(error)) return null;
    throw error;
  }
}

export async function getActivityHeatmap(): Promise<ActivityHeatmap | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) return null;

  try {
    return await apiFetch<ActivityHeatmap>("/api/v1/admin/dashboard/activity-heatmap", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (error) {
    if (isUnauthorized(error)) return null;
    throw error;
  }
}

export async function getAlerts(): Promise<DashboardAlert[]> {
  const accessToken = await getAccessToken();
  if (!accessToken) return [];

  try {
    return await apiFetch<DashboardAlert[]>("/api/v1/admin/dashboard/alerts", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (error) {
    if (isUnauthorized(error)) return [];
    throw error;
  }
}

export async function getSystemHealth(): Promise<SystemHealth | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) return null;

  try {
    return await apiFetch<SystemHealth>("/api/v1/admin/dashboard/system-health", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (error) {
    if (isUnauthorized(error)) return null;
    throw error;
  }
}
