// Mirrors apps/api's ACCESS_TOKEN_EXPIRE_MINUTES / REFRESH_TOKEN_EXPIRE_DAYS
// (core/config.py). Cookie lifetimes are advisory (the JWTs carry their own
// `exp`), but keeping them in sync avoids the browser holding onto a cookie
// for a token the API has already stopped accepting.
export const ACCESS_TOKEN_COOKIE = "arutech_access_token";
export const REFRESH_TOKEN_COOKIE = "arutech_refresh_token";

const ACCESS_TOKEN_MAX_AGE_SECONDS = 15 * 60;
const REFRESH_TOKEN_MAX_AGE_SECONDS = 30 * 24 * 60 * 60;

export interface SessionCookieOptions {
  httpOnly: true;
  secure: boolean;
  sameSite: "lax";
  path: "/";
  maxAge: number;
}

function cookieOptions(maxAgeSeconds: number): SessionCookieOptions {
  return {
    httpOnly: true,
    // Off in dev so http://localhost still works; every real deployment
    // terminates TLS in front of this app (see infra/nginx).
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: maxAgeSeconds,
  };
}

export const accessTokenCookieOptions = (): SessionCookieOptions =>
  cookieOptions(ACCESS_TOKEN_MAX_AGE_SECONDS);

export const refreshTokenCookieOptions = (): SessionCookieOptions =>
  cookieOptions(REFRESH_TOKEN_MAX_AGE_SECONDS);
