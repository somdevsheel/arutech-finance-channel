import { apiFetch, ApiError } from "@/lib/api-client";
import type { TokenResponse } from "@/types/auth";

/**
 * Pure fetch — no `next/headers` — so it's safe to call from proxy.ts
 * (which reads/writes cookies via NextRequest/NextResponse, not the
 * cookies() API) as well as from Server Actions and Server Components.
 */
export async function refreshTokens(
  refreshToken: string,
  forwardHeaders?: Record<string, string>,
): Promise<TokenResponse | null> {
  try {
    return await apiFetch<TokenResponse>("/api/v1/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
      headers: forwardHeaders,
    });
  } catch (error) {
    if (error instanceof ApiError) return null;
    throw error;
  }
}
