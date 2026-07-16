# Phase 2 — Authentication, Authorization, RBAC

Status: complete. Builds directly on Phase 1's `core/security.py`
primitives and bare `User` model — see `docs/phase-1-architecture.md` for
that foundation.

## Scope

Real login/logout, OTP-based passwordless login, password reset, refresh-
token rotation with reuse detection, a full RBAC schema with permission
enforcement, and a populated audit log. Explicitly out of scope: the admin
UI for managing roles/permissions (Phase 9 — this phase builds the schema
and enforcement mechanism Phase 9's UI will drive), real SMS/email delivery
(Phase 13 — this phase builds the `OtpDeliveryPort` interface and a
logging-only adapter), and email verification (not in the platform's
Phase 2 checklist; `users.is_verified` is untouched here).

## Layering

```
domain/auth/       RefreshTokenEntity, OtpEntity, OtpPurpose.
                    RefreshTokenRepository / OtpRepository interfaces.
                    OtpDeliveryPort interface (send a code somewhere).
domain/rbac/       RoleEntity, PermissionEntity, RbacRepository interface.
domain/audit/      AuditLogEntity, AuditLogRepository interface.
infrastructure/    SQLAlchemy models (rbac.py, auth.py) + the concrete
                    repositories implementing the interfaces above.
                    notifications/log_otp_delivery.py: the Phase 2
                    OtpDeliveryPort adapter (logs the code).
                    database/seed_data.py: the roles/permissions seed data,
                    imported by both the migration and the test suite so
                    there's one source of truth, not two hand-maintained
                    copies that can drift.
services/          auth_service.py (the use-case layer: register, login,
                    OTP request/verify, refresh, logout, password reset,
                    sessions) and audit_service.py (thin wrapper the
                    former calls into on every auth-relevant action).
api/deps.py         FastAPI Depends wiring: get_current_user,
                    require_permission(code), repository/service providers.
api/v1/schemas/auth.py   Request/response DTOs. Not under domain/ — see
                          "what changed from the Phase 1 plan" below.
api/v1/endpoints/auth.py The HTTP surface.
```

### What changed from the Phase 1 plan

Phase 1's doc sketched request/response schemas living under
`domain/users/schemas.py`. In practice they ended up in
`api/v1/schemas/auth.py` instead: domain stays framework-agnostic (no
Pydantic), and request/response shape is an HTTP-contract concern, not a
business one. Small correction, worth recording so nobody goes looking for
schemas in `domain/` later.

## Key design decisions

**RBAC is a real many-to-many schema, not a hardcoded permission map.**
`roles` / `permissions` / `role_permissions` / `user_roles`. Phase 9 needs
roles and permissions to be admin-editable, which means they have to live
in the database from the start — retrofitting that onto a code-constant
permission map later would mean redesigning the schema after data already
exists. `users.role` (the Phase 1 enum) stays the coarse actor type/portal
selector; these tables carry fine-grained permissions within that.

**Permissions are re-fetched from the DB on every `require_permission`
call, not embedded in the access token's claims.** The access token does
carry `role` (cheap, coarse, fine to cache in a claim), but permission
checks always hit the DB fresh. Slightly more DB load per permission-gated
request; in exchange, revoking a permission takes effect on the very next
request instead of waiting out the access token's 15-minute lifetime. The
right tradeoff for a fintech platform.

**Refresh tokens are stored server-side, hashed (HMAC-SHA256), keyed by the
JWT's `jti`.** This is what makes "Session Management" real rather than
aspirational: `GET /auth/sessions` lists them, `DELETE
/auth/sessions/{id}` revokes one. Reusing an already-rotated refresh token
revokes *every* session for that user, not just the one — standard
rotation/theft-detection practice, and covered by
`test_reusing_a_rotated_refresh_token_revokes_all_sessions`.

**OTPs are hashed with HMAC-SHA256, not Argon2.** Argon2's slow,
memory-hard design is for password storage where an attacker might brute
force a stolen hash offline. A 6-digit OTP has only a million possible
values and is inherently short-lived and rate-limited (3 requests/minute,
5 verify attempts before lockout) — the attempt cap and expiry are the real
defense, and a slow hash would just add latency to every login for no
security benefit. Same rationale applies to refresh-token hashing.

**Public `/auth/register` only ever creates `customer` accounts.**
Employee/partner/admin accounts are provisioned by admins (Phase 9/10/11
territory) — there's deliberately no public API path to self-register into
a privileged role.

**Login, OTP-request, and password-reset-request all give identical
generic responses regardless of whether the email exists.** No user
enumeration. Verified explicitly:
`test_login_with_unknown_email_gives_same_generic_error`,
`test_otp_request_for_unknown_email_is_silently_ok`,
`test_reset_request_for_unknown_email_is_silently_ok`.

**Refresh tokens come back in the JSON response body, not a cookie.**
Works uniformly for mobile apps, partner-API integrations, and the web
frontend alike. When Phase 4 builds the customer-portal BFF, it can choose
to move the web client specifically onto httpOnly cookies at that layer
without this API's contract changing.

## Database schema (migration `c422da52af08`)

`roles`(id, name, description, is_system) · `permissions`(id, code,
description) · `role_permissions`(role_id, permission_id) ·
`user_roles`(user_id, role_id) · `refresh_tokens`(id, user_id, jti,
token_hash, expires_at, revoked_at, user_agent, ip_address) ·
`otp_codes`(id, user_id, purpose[login|password_reset], code_hash,
expires_at, consumed_at, attempts).

Seed data (via `infrastructure/database/seed_data.py`, shared with the test
suite): roles matching the Phase 1 enum (admin/employee/partner/customer);
a small honest permission set — `users.read`, `users.manage`,
`audit_logs.read`, `roles.manage` — mapped admin-gets-everything,
employee-gets-read-only; nothing invented for loan/CRM features that don't
exist yet. Any user that existed *before* this migration is backfilled into
`user_roles` based on their existing `role` column.

## APIs

`POST /auth/register` · `POST /auth/login` · `POST /auth/otp/request` ·
`POST /auth/otp/verify` · `POST /auth/refresh` · `POST /auth/logout` ·
`POST /auth/logout-all` · `POST /auth/password-reset/request` · `POST
/auth/password-reset/confirm` · `GET /auth/me` · `GET /auth/sessions` ·
`DELETE /auth/sessions/{id}` · `GET /auth/audit-logs` (permission-gated on
`audit_logs.read` — the endpoint that proves `require_permission` actually
works, not just compiles).

## Security

Argon2id passwords (Phase 1) + HMAC-hashed OTPs and refresh tokens +
rotated/revocable/reuse-detected sessions + per-route rate limits tighter
than the global default on every unauthenticated auth endpoint (register
5/min, login 10/min, OTP request 3/min, OTP verify 10/min, refresh 20/min,
password-reset request 3/min, confirm 5/min) + no user-enumeration anywhere
+ every auth-relevant action audit-logged with actor, action, and metadata.

## Bugs found building this phase (and why they matter for later phases)

**Coverage.py silently under-reported async code by ~50%.** Without
`concurrency = ["greenlet", "thread"]` in `[tool.coverage.run]`,
`auth_service.py` showed 49% coverage — appearing to miss entire method
bodies, including ones with tests that explicitly assert their exact
branch behavior. Cause: SQLAlchemy's async engine bridges to sync DBAPI
calls via `greenlet_spawn`, and coverage.py's default tracer loses the
calling frame across that switch unless told about the concurrency model.
Fixed once, in `pyproject.toml`; this would otherwise have produced
misleading coverage numbers for **every** future phase that touches the
database from async code, not just this one.

**Rate limiter state leaked across tests.** `slowapi`'s `Limiter` is a
process-wide singleton even when pointed at `memory://` storage for tests.
Every test client request looks like it comes from `127.0.0.1`, so hit
counts accumulated across the whole test *session*, not per-test — a
5/minute limit on `/auth/register` meant the 6th test anywhere in the
suite that registered a user got a spurious 429. Fixed with an autouse
`limiter.reset()` fixture in `conftest.py`.

**Postgres enum types need an explicit drop on downgrade** — same class of
bug as Phase 1's `user_role`, this time for `otp_purpose`. `op.drop_table`
never drops the native enum type it created; without an explicit
`sa.Enum(name=...).drop(...)` in `downgrade()`, a downgrade→upgrade cycle
fails with "type already exists." Caught by the same CI migration-cycle
check Phase 1 added.

**`email-validator` rejects `.test` as a TLD** (it's flagged as
special-use/non-deliverable), which broke every test using
`user@arutech.test`-style addresses. Test fixtures now use `example.com`,
the domain RFC 2606 actually reserves for documentation and that
`email-validator` accepts.
