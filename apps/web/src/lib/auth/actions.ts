"use server";

import { cookies } from "next/headers";
import { apiFetch, ApiError } from "@/lib/api-client";
import {
  ACCESS_TOKEN_COOKIE,
  REFRESH_TOKEN_COOKIE,
  accessTokenCookieOptions,
  refreshTokenCookieOptions,
} from "@/lib/auth/constants";
import { getForwardedRequestHeaders } from "@/lib/auth/request-context";
import { getAccessTokenOrThrow } from "@/lib/auth/session";
import {
  loginSchema,
  otpRequestSchema,
  otpVerifySchema,
  passwordResetConfirmSchema,
  passwordResetRequestSchema,
  registerSchema,
} from "@/lib/auth/schemas";
import type { AuthUser, TokenResponse } from "@/types/auth";

export type ActionResult<T = undefined> =
  | { ok: true; data: T }
  | { ok: false; error: string };

function fail(error: unknown): { ok: false; error: string } {
  const message =
    error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
  return { ok: false, error: message };
}

async function persistSession(tokens: TokenResponse): Promise<void> {
  const store = await cookies();
  store.set(ACCESS_TOKEN_COOKIE, tokens.access_token, accessTokenCookieOptions());
  store.set(REFRESH_TOKEN_COOKIE, tokens.refresh_token, refreshTokenCookieOptions());
}

async function clearSession(): Promise<void> {
  const store = await cookies();
  store.delete(ACCESS_TOKEN_COOKIE);
  store.delete(REFRESH_TOKEN_COOKIE);
}

export async function loginAction(input: unknown): Promise<ActionResult<{ user: AuthUser }>> {
  const parsed = loginSchema.safeParse(input);
  if (!parsed.success) return { ok: false, error: "Enter a valid email and password." };

  try {
    const headers = await getForwardedRequestHeaders();
    const result = await apiFetch<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: parsed.data,
      headers,
    });
    await persistSession(result);
    return { ok: true, data: { user: result.user } };
  } catch (error) {
    return fail(error);
  }
}

export async function registerAction(
  input: unknown,
): Promise<ActionResult<{ user: AuthUser }>> {
  const parsed = registerSchema.safeParse(input);
  if (!parsed.success) return { ok: false, error: "Check the highlighted fields and try again." };

  const { full_name, email, phone, password } = parsed.data;
  try {
    const headers = await getForwardedRequestHeaders();
    const user = await apiFetch<AuthUser>("/api/v1/auth/register", {
      method: "POST",
      body: { full_name, email, phone: phone || null, password },
      headers,
    });
    return { ok: true, data: { user } };
  } catch (error) {
    return fail(error);
  }
}

export async function requestOtpAction(input: unknown): Promise<ActionResult> {
  const parsed = otpRequestSchema.safeParse(input);
  if (!parsed.success) return { ok: false, error: "Enter a valid email address." };

  try {
    const headers = await getForwardedRequestHeaders();
    await apiFetch("/api/v1/auth/otp/request", { method: "POST", body: parsed.data, headers });
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function verifyOtpAction(
  input: unknown,
): Promise<ActionResult<{ user: AuthUser }>> {
  const parsed = otpVerifySchema.safeParse(input);
  if (!parsed.success) return { ok: false, error: "Enter the 6-digit code sent to your email." };

  try {
    const headers = await getForwardedRequestHeaders();
    const result = await apiFetch<TokenResponse>("/api/v1/auth/otp/verify", {
      method: "POST",
      body: parsed.data,
      headers,
    });
    await persistSession(result);
    return { ok: true, data: { user: result.user } };
  } catch (error) {
    return fail(error);
  }
}

export async function requestPasswordResetAction(input: unknown): Promise<ActionResult> {
  const parsed = passwordResetRequestSchema.safeParse(input);
  if (!parsed.success) return { ok: false, error: "Enter a valid email address." };

  try {
    const headers = await getForwardedRequestHeaders();
    await apiFetch("/api/v1/auth/password-reset/request", {
      method: "POST",
      body: parsed.data,
      headers,
    });
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function confirmPasswordResetAction(input: unknown): Promise<ActionResult> {
  const parsed = passwordResetConfirmSchema.safeParse(input);
  if (!parsed.success) return { ok: false, error: "Check the code and new password and try again." };

  try {
    const headers = await getForwardedRequestHeaders();
    await apiFetch("/api/v1/auth/password-reset/confirm", {
      method: "POST",
      body: parsed.data,
      headers,
    });
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function logoutAction(): Promise<ActionResult> {
  const store = await cookies();
  const refreshToken = store.get(REFRESH_TOKEN_COOKIE)?.value;

  try {
    if (refreshToken) {
      const headers = await getForwardedRequestHeaders();
      await apiFetch("/api/v1/auth/logout", {
        method: "POST",
        body: { refresh_token: refreshToken },
        headers,
      });
    }
  } catch {
    // Best-effort: the local session is cleared below regardless of
    // whether the API call succeeded, so the browser is signed out either way.
  } finally {
    await clearSession();
  }

  return { ok: true, data: undefined };
}

export async function logoutAllAction(): Promise<ActionResult> {
  try {
    const accessToken = await getAccessTokenOrThrow();
    const headers = await getForwardedRequestHeaders();
    await apiFetch("/api/v1/auth/logout-all", {
      method: "POST",
      headers: { ...headers, Authorization: `Bearer ${accessToken}` },
    });
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  } finally {
    await clearSession();
  }
}

export async function revokeSessionAction(sessionId: string): Promise<ActionResult> {
  try {
    const accessToken = await getAccessTokenOrThrow();
    const headers = await getForwardedRequestHeaders();
    await apiFetch(`/api/v1/auth/sessions/${sessionId}`, {
      method: "DELETE",
      headers: { ...headers, Authorization: `Bearer ${accessToken}` },
    });
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}
