# Phase 4 — Customer Portal

Status: complete. Builds on Phase 2's auth/RBAC API (unchanged — no new
endpoints, no migration) and Phase 1's app shell.

## Scope

A signed-in customer portal: password and OTP login, registration,
password reset, a dashboard shell, a read-only profile view, and
session/device management (list + revoke + sign-out-everywhere). Explicitly
out of scope: loan application submission and tracking (LOS — later
phases), profile editing (needs a `PATCH /users/me` endpoint that doesn't
exist yet), and email verification UI (`users.is_verified` still isn't
driven by anything, per Phase 2's note).

This is the phase Phase 2's doc pointed at: "when Phase 4 builds the
customer-portal BFF, it can choose to move the web client specifically
onto httpOnly cookies... without this API's contract changing." That's
exactly what happened — `apps/api` gained zero new auth endpoints; only
`apps/web` changed, plus one backend fix described below.

## The BFF pattern

Phase 2's API returns `{ access_token, refresh_token, user }` in the JSON
body, deliberately transport-agnostic (mobile apps, partner integrations,
and the web frontend all read the same contract). The web app is the one
client that gets to choose httpOnly cookies instead of handling raw
tokens in JS — and Next.js 16 renamed the mechanism that makes this a
one-hop pattern rather than a proxied API from `middleware.ts` to
`proxy.ts` (`middleware` is deprecated in 16.0). This phase uses:

```
src/lib/auth/
  constants.ts        Cookie names + options (httpOnly, sameSite=lax,
                       secure in production only — see "bugs found").
  schemas.ts           Zod schemas — the single source of truth for both
                        client-side RHF validation and server-action
                        re-validation, mirroring apps/api's own
                        _validate_password_strength rules.
  actions.ts            "use server" Server Actions: login, register,
                         requestOtp, verifyOtp, requestPasswordReset,
                         confirmPasswordReset, logout, logoutAll,
                         revokeSession. Each calls the API directly
                         (server-to-server) and is the only place that
                         sets/clears the session cookies.
  session.ts             Read-only helpers (getCurrentUser,
                          getActiveSessions) for Server Components. No
                          cookie writes — Server Components can't set
                          cookies (only Server Actions/Route Handlers
                          can); see "why proxy.ts owns refresh" below.
  refresh.ts              Pure fetch, no next/headers import — the one
                           piece reused by both proxy.ts (NextRequest/
                           NextResponse cookies) and Server Actions
                           (next/headers cookies()).
  request-context.ts       Forwards the real visitor's IP/User-Agent from
                            Server Actions to the API (see "bugs found").
src/proxy.ts                 Gates /dashboard, /profile, /sessions;
                              silently refreshes the access token.
src/app/(auth)/               login, register, forgot-password — public.
src/app/(portal)/             layout (auth-gated) + dashboard, profile,
                               sessions.
```

**Server Actions, not Route Handlers, for the mutation surface.** Next's
own "Backend for Frontend" guide frames both as valid; Server Actions win
here because RHF's `handleSubmit` can call an imported `"use server"`
function directly as an async callback — no separate `route.ts` per verb,
no hand-rolled fetch wrapper on the client, and `cookies().set()` is only
legal inside a Server Action or Route Handler in the first place. The
existing marketing `ContactForm` (Phase 3) calls the API straight from the
browser via `apiFetch`; this phase doesn't touch that pattern; it adds a
second, cookie-owning one for anything that establishes or ends a session.

**Why proxy.ts owns the refresh, and Server Components/Actions don't.**
Next.js does not allow setting cookies during a Server Component render —
only inside a Server Action or Route Handler. That rules out a
"refresh-on-read" helper called from `dashboard/page.tsx` et al. Instead,
`proxy.ts` matches every portal route (pages *and*, per Next's docs, the
Server Actions invoked from them — Server Functions are handled as POST
requests to the page they're used from, so they inherit the page's Proxy
coverage) and refreshes once, before anything downstream runs. Pages and
actions under `(portal)/` can therefore assume the access cookie is
already fresh and just read it — see the comment in `session.ts`.

**Defense in depth, not defense-by-proxy-alone.** Next's own Route
Handlers guide is explicit: "Always verify authentication... rather than
relying on Proxy alone" — a matcher typo silently removes coverage.
`(portal)/layout.tsx` independently calls `getCurrentUser()` and redirects
to `/login` if it's null, regardless of what `proxy.ts` did.

**Refresh tokens still never reach client JS.** Server Actions return a
plain `{ ok, data | error }` result — the raw `TokenResponse` never
crosses the server/client boundary; only `{ user }` does.

**Reset flow uses a 6-digit code, not a magic-link token**, because
that's what Phase 2's `POST /auth/password-reset/confirm` accepts
(`email + code + new_password`). No tokenized-link scheme exists yet, so
`forgot-password/page.tsx` is a two-step form (request code → enter code
+ new password) on one route rather than a `reset-password?token=...`
page.

## Bugs found building this phase

**Routing customer-portal traffic through the BFF broke Phase 2's
IP-based defenses — and the bug already existed, just less visibly.**
`get_remote_address` (rate limiting) and `get_client_ip` (audit logging)
both read `request.client.host`, the raw TCP peer. Once `apps/web` calls
the API server-to-server, every customer-portal login/register/OTP
request arrives from the `web` container, not the visitor — collapsing
Phase 2's per-route rate limits (10/min login, 3/min OTP, etc.) onto one
shared bucket for every customer, and writing the wrong IP into every
auth-relevant audit log entry. (The same gap existed pre-Phase-4 for
anything behind nginx, since nothing in `main.py` trusted proxy headers
either — it just had no traffic exercising it yet.)

Fixed with `uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware`,
added as the outermost middleware (so `request.client` is corrected
before SlowAPI, audit logging, or anything else reads it) and scoped to a
new `TRUSTED_PROXY_IPS` setting — defaults to `127.0.0.1` (trust nothing
by default, matching the "insecure by default only in dev" posture
elsewhere in this codebase), raised to the compose network's
`172.28.0.0/16` subnet for the `api` service in `docker-compose.yml`,
where nginx and `web` are the only things that can reach it internally.
`apps/web`'s `request-context.ts` and `proxy.ts` forward whatever
`X-Forwarded-For`/`User-Agent` they received onward, so the real visitor
IP survives the extra hop. Verified end-to-end in
`test_trusted_proxy.py`: a forwarded header is honored from a trusted
peer and ignored from an untrusted one (an internet-facing caller
spoofing `X-Forwarded-For` must not be able to fake its way past a rate
limit or falsify the audit trail). Real production trusted-proxy topology
is deployment-phase territory, same deferral Phase 1 made for full OWASP
hardening (Phase 16).

**A naive "redirect logged-in visitors away from /login" rule in
`proxy.ts` created an infinite redirect loop.** The obvious approach —
`proxy.ts` sends anyone with an access cookie from `/login` to
`/dashboard` — trusts cookie *presence* as proof of a valid session. It
isn't: a present-but-invalid access token (signing key rotated under a
still-open tab is the realistic trigger, and this codebase regenerates a
dev JWT keypair per the README's setup step) sends the visitor to
`/dashboard`, where `(portal)/layout.tsx` finds the token invalid and
redirects back to `/login`, which redirects to `/dashboard` again,
forever — with no way back to a working sign-in page short of clearing
cookies by hand. Fixed by moving that redirect out of `proxy.ts` (which
only checks cookie presence) and into `login/page.tsx` /
`register/page.tsx` themselves, which call `getCurrentUser()` — an actual
`GET /auth/me` round trip — before deciding to redirect.

**`middleware.ts` is deprecated in Next.js 16** (renamed to `proxy.ts`,
default export renamed `middleware` → `proxy`) — caught before writing
any code by reading `node_modules/next/dist/docs` per `apps/web/AGENTS.md`
rather than from training-data familiarity with older Next.js versions.
Worth calling out explicitly since every future phase touching routing,
route handlers, or dynamic params in `apps/web` should do the same check
first — this version has diverged from what pretraining knows about
"Next.js" in more than this one place.

## Security

Every session-establishing/ending action (login, register, OTP verify,
password reset, logout) is a Server Action, so it's protected by Next's
built-in Origin-header check for Server Actions — an extra CSRF layer on
top of `sameSite=lax` cookies (which alone already block cross-site
*POST*s; `lax` still allows the cookie on top-level cross-site
*navigation*, which is what login/logout require to work after a
redirect). Cookies are `httpOnly` (unreadable from JS — no XSS-driven
token theft) and `secure` in every environment except local dev over
plain HTTP. Password/OTP/reset payloads are re-validated server-side with
the same Zod schemas the client uses, not just trusted from the client.

## Known limitations (honest, not deferred silently)

- The sessions table doesn't flag which row is the caller's *current*
  device — doing that needs decoding the refresh JWT's `jti` client-side,
  which isn't worth the complexity yet for a list that's usually 1-2 rows
  long.
- In plain `pnpm dev` (no nginx in front), there's no `X-Forwarded-For` to
  forward, so audit-log IPs for that setup show the Next.js dev server's
  address — unchanged from before this phase, and only a local-dev
  cosmetic gap.
