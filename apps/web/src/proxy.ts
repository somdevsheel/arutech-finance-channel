import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import {
  ACCESS_TOKEN_COOKIE,
  REFRESH_TOKEN_COOKIE,
  accessTokenCookieOptions,
  refreshTokenCookieOptions,
} from "@/lib/auth/constants";
import { refreshTokens } from "@/lib/auth/refresh";

const PORTAL_PREFIXES = ["/dashboard", "/profile", "/sessions"];

function matchesPrefix(pathname: string, prefixes: string[]): boolean {
  return prefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

function redirectToLogin(request: NextRequest): NextResponse {
  const url = new URL("/login", request.url);
  url.searchParams.set("next", request.nextUrl.pathname);
  return NextResponse.redirect(url);
}

/**
 * Gates the customer portal and does the one silent token refresh that
 * makes a 15-minute access token invisible to the user during a longer
 * session. Server Components and Server Actions on these routes assume
 * the access cookie is already fresh by the time they run — this is the
 * only place it's refreshed. See docs/phase-4-architecture.md.
 *
 * Deliberately doesn't also redirect an already-authenticated visitor
 * away from /login or /register: that would mean trusting cookie
 * *presence* as proof of a valid session, and it isn't — a present but
 * invalid/expired access token (e.g. the API's signing key rotated under
 * a still-open tab) would bounce /login -> /dashboard -> (layout finds
 * the token invalid) -> /login forever. login/page.tsx and
 * register/page.tsx do that redirect themselves, after actually
 * verifying the session via getCurrentUser().
 */
export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (!matchesPrefix(pathname, PORTAL_PREFIXES)) {
    return NextResponse.next();
  }

  const accessToken = request.cookies.get(ACCESS_TOKEN_COOKIE)?.value;
  const refreshToken = request.cookies.get(REFRESH_TOKEN_COOKIE)?.value;

  if (accessToken) {
    return NextResponse.next();
  }

  if (!refreshToken) {
    return redirectToLogin(request);
  }

  const forwardHeaders: Record<string, string> = {};
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) forwardHeaders["X-Forwarded-For"] = forwardedFor;
  const userAgent = request.headers.get("user-agent");
  if (userAgent) forwardHeaders["User-Agent"] = userAgent;

  const refreshed = await refreshTokens(refreshToken, forwardHeaders);
  if (!refreshed) {
    const response = redirectToLogin(request);
    response.cookies.delete(ACCESS_TOKEN_COOKIE);
    response.cookies.delete(REFRESH_TOKEN_COOKIE);
    return response;
  }

  // Update the request's cookie jar too, not just the response's, so the
  // Server Component render that follows in this same request sees the
  // fresh token instead of the stale one it arrived with.
  request.cookies.set(ACCESS_TOKEN_COOKIE, refreshed.access_token);
  request.cookies.set(REFRESH_TOKEN_COOKIE, refreshed.refresh_token);

  const response = NextResponse.next({ request });
  response.cookies.set(ACCESS_TOKEN_COOKIE, refreshed.access_token, accessTokenCookieOptions());
  response.cookies.set(REFRESH_TOKEN_COOKIE, refreshed.refresh_token, refreshTokenCookieOptions());
  return response;
}

export const config = {
  matcher: ["/dashboard/:path*", "/profile/:path*", "/sessions/:path*"],
};
