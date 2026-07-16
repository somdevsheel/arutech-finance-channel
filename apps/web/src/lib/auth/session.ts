import { cookies } from "next/headers";
import { apiFetch, ApiError } from "@/lib/api-client";
import { ACCESS_TOKEN_COOKIE } from "@/lib/auth/constants";
import type { AuthSession, AuthUser } from "@/types/auth";

// Read-only by design: Server Components can't set cookies (only Server
// Actions and Route Handlers can), so there's no safe way to persist a
// refreshed token from here. proxy.ts refreshes the access cookie before
// any portal route renders (see its matcher), so by the time these run
// the cookie is already current — see docs/phase-4-architecture.md.

export async function getAccessToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(ACCESS_TOKEN_COOKIE)?.value ?? null;
}

export async function getAccessTokenOrThrow(): Promise<string> {
  const token = await getAccessToken();
  if (!token) throw new ApiError(401, "Not authenticated", null);
  return token;
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) return null;

  try {
    return await apiFetch<AuthUser>("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export async function getActiveSessions(): Promise<AuthSession[]> {
  const accessToken = await getAccessToken();
  if (!accessToken) return [];

  try {
    return await apiFetch<AuthSession[]>("/api/v1/auth/sessions", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return [];
    throw error;
  }
}
