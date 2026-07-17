import { apiFetch, ApiError } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth/session";
import type {
  ActivityHeatmap,
  DashboardAlert,
  ExecutiveKpis,
  LeadFunnel,
  SystemHealth,
} from "@/types/dashboard";
import type {
  AdminUser,
  AuditLogEntry,
  BlogPost,
  Lender,
  LoanProduct,
  NotificationTemplate,
  Permission,
  Role,
  SystemSetting,
} from "@/types/admin";

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

// Phase 9's admin subsystems (RBAC, Lenders, Loan Products, Notification
// Templates, CMS, Settings) all share this exact list-fetch shape, so
// this one generic helper replaces what would otherwise be ~15 copies of
// the same try/catch.
async function fetchAdminList<T>(path: string): Promise<T[]> {
  const accessToken = await getAccessToken();
  if (!accessToken) return [];

  try {
    return await apiFetch<T[]>(path, { headers: { Authorization: `Bearer ${accessToken}` } });
  } catch (error) {
    if (isUnauthorized(error)) return [];
    throw error;
  }
}

async function fetchAdminOne<T>(path: string): Promise<T | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) return null;

  try {
    return await apiFetch<T>(path, { headers: { Authorization: `Bearer ${accessToken}` } });
  } catch (error) {
    if (isUnauthorized(error)) return null;
    throw error;
  }
}

export async function getUsers(params?: {
  role?: string;
  is_active?: boolean;
}): Promise<AdminUser[]> {
  const query = new URLSearchParams();
  if (params?.role) query.set("role", params.role);
  if (params?.is_active !== undefined) query.set("is_active", String(params.is_active));
  const qs = query.toString();
  return fetchAdminList<AdminUser>(`/api/v1/admin/users${qs ? `?${qs}` : ""}`);
}

export async function getUser(userId: string): Promise<AdminUser | null> {
  return fetchAdminOne<AdminUser>(`/api/v1/admin/users/${userId}`);
}

export async function getRoles(): Promise<Role[]> {
  return fetchAdminList<Role>("/api/v1/admin/roles");
}

export async function getRolePermissions(roleId: string): Promise<Permission[]> {
  return fetchAdminList<Permission>(`/api/v1/admin/roles/${roleId}/permissions`);
}

export async function getPermissions(): Promise<Permission[]> {
  return fetchAdminList<Permission>("/api/v1/admin/permissions");
}

export async function getLenders(): Promise<Lender[]> {
  return fetchAdminList<Lender>("/api/v1/lenders");
}

export async function getLoanProducts(): Promise<LoanProduct[]> {
  return fetchAdminList<LoanProduct>("/api/v1/loan-products");
}

export async function getNotificationTemplates(): Promise<NotificationTemplate[]> {
  return fetchAdminList<NotificationTemplate>("/api/v1/notification-templates");
}

export async function getBlogPosts(): Promise<BlogPost[]> {
  return fetchAdminList<BlogPost>("/api/v1/cms/blog-posts");
}

export async function getBlogPost(postId: string): Promise<BlogPost | null> {
  return fetchAdminOne<BlogPost>(`/api/v1/cms/blog-posts/${postId}`);
}

export async function getSettings(): Promise<SystemSetting[]> {
  return fetchAdminList<SystemSetting>("/api/v1/admin/settings");
}

export async function getAuditLogs(): Promise<AuditLogEntry[]> {
  return fetchAdminList<AuditLogEntry>("/api/v1/auth/audit-logs");
}
