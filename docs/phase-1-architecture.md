# Phase 1 — System Architecture & Foundation

Status: complete. This document records the decisions behind the
foundation so later phases (and later readers) don't have to reverse-engineer
the "why."

## Scope

Phase 1 delivers the platform skeleton every later phase builds on:
monorepo + tooling, Docker/Compose, CI, the database foundation (models +
migrations + repository pattern), the authentication *primitives* (password
hashing, JWT issuance/verification — not login/OTP/RBAC flows, which are
Phase 2), logging, configuration, and monitoring.

It deliberately does **not** include: public marketing pages (Phase 3),
customer/employee/partner portals (Phases 4, 10, 11), RBAC (Phase 2), or
OWASP hardening beyond a baseline (Phase 16). Building those now would mean
guessing at requirements the later phases define explicitly.

## Monorepo shape

pnpm workspaces (`apps/*`, `packages/*`) + Turborepo. No `packages/ui` yet:
there is exactly one frontend consumer (`apps/web`), so a shared component
package would be premature abstraction. It gets extracted once a second
frontend app (admin/employee/partner portal) actually needs the same
components — cheap to do then, wasted effort now.

## Backend: clean architecture / DDD layering

```
api/             FastAPI routers (versioned, /api/v1). HTTP concerns only.
services/        Use-case orchestration. Empty in Phase 1 — nothing to
                 orchestrate yet beyond what the health endpoints do
                 directly; Phase 2 adds auth_service.py etc.
domain/          Entities + repository *interfaces*. Zero framework
                 imports — domain/users/entities.py has no SQLAlchemy or
                 FastAPI dependency.
infrastructure/  SQLAlchemy models + repository *implementations*
                 (adapters). Depends on domain, never the reverse.
core/            Cross-cutting: config, security, logging, database engine,
                 redis client, telemetry, middleware, exception handling.
```

Dependency injection is FastAPI's own `Depends` graph bound to interfaces —
no `dependency-injector` or similar framework. With one repository and no
services yet, that would be solving a problem Phase 1 doesn't have.

## Key decisions

**uv, not Poetry.** Poetry wasn't installed in the target environment; uv is
a faster, single-binary, first-class-lockfile tool that's become standard in
production FastAPI shops. No functional difference for this project, just
faster installs and simpler CI.

**Async SQLAlchemy 2.0 + asyncpg, not sync.** The business goal is "support
millions of users." A thread-pool-per-request model doesn't get there;
async I/O does. This has to be decided at the foundation — retrofitting
async onto a sync codebase later is a rewrite, not a refactor.

**Repository pattern with ABCs in `domain/`, SQLAlchemy adapter in
`infrastructure/`.** `UserRepository` (interface) vs.
`SqlAlchemyUserRepository` (implementation) means: (1) services can be unit
tested against an in-memory fake without a database, (2) swapping
persistence later (read replicas, a different store for a specific portal)
means adding an adapter, not touching callers. Proven in Phase 1 itself: the
repository is tested against SQLite in-memory in CI, and runs on Postgres in
every real environment, with zero repository code aware of which.

**`Uuid` (SQLAlchemy 2.0 generic type), not `dialects.postgresql.UUID`.**
The generic type renders as native `uuid` on Postgres and as `CHAR(32)` on
SQLite — which is what makes the SQLite-backed repository tests possible at
all. This was a real bug caught during Phase 1 build-out: the Postgres-only
type would have silently made the "fast, no-Docker-needed" repository tests
impossible.

**Postgres enum stores the `StrEnum`'s `.value`, not its member `.name`.**
SQLAlchemy's `Enum(SomeEnum)` defaults to storing the Python member *name*
(`"CUSTOMER"`) in the database column, not the string value (`"customer"`)
that the same enum serializes to in JSON responses. Left alone, the raw DB
value and the API's wire representation would silently diverge. Fixed via
`values_callable` on the `user_role` column — see
`infrastructure/database/models/user.py`.

**RS256 (asymmetric), not HS256, for JWTs.** Only the primitives ship in
Phase 1 (`core/security.py`) — real login/OTP/refresh-rotation is Phase 2 —
but the algorithm choice has to be made now because it's baked into every
token issued afterward. RS256 means any future service (partner API, a
mobile app, a read-only reporting service) can verify tokens with the public
key alone, without ever holding the signing secret.

**Argon2id for password hashing**, via `passlib`. Current OWASP
recommendation over bcrypt.

**`users.role` is a plain enum column, not a full RBAC schema.**
Roles/permissions/role-bindings tables are explicitly Phase 2 scope
("Authorization / RBAC" in the platform plan). Building that schema now
would mean guessing at Phase 2's design and likely redoing it.

**Structured logging + OpenTelemetry from commit one.** `structlog` (JSON
logs) + OTel auto-instrumentation of FastAPI/SQLAlchemy/Redis, exported via
OTLP to an `otel-collector` container (which itself only logs to stdout in
Phase 1 — swapping in Tempo/Jaeger/a vendor backend is a one-line config
change, not a code change). Retrofitting observability into a live
multi-tenant fintech system is expensive; every request gets a correlation
ID from day one via `RequestContextMiddleware`.

**Alembic migrations only.** `Base.metadata.create_all` is never called
outside of test fixtures (where an ephemeral SQLite DB is created and thrown
away per test). Every real schema change is a reviewable migration file. CI
enforces this further: it runs `upgrade head` → `downgrade base` → `upgrade
head` on every PR, which catches migrations that apply but don't reverse
cleanly (this caught a real bug in Phase 1: the initial migration dropped
the `users` table but not the Postgres enum type it created, which broke
`downgrade` → `upgrade`).

**Rate limiting is Redis-backed (`slowapi` + `limits`), not in-memory.**
An in-memory limiter only limits a single process; this platform needs to
scale horizontally, so limits must be shared across instances from the
start. The one exception is the test suite, which points the limiter at
`memory://` via a dedicated `RATE_LIMIT_STORAGE_URI` setting — tests
shouldn't need a live Redis just to exercise the app, but production
defaults to sharing `REDIS_URL`.

**Fail-fast config.** `get_settings()` raises at startup — not at first
request — if `ENVIRONMENT` is `staging`/`production` and secrets
(`SECRET_KEY`, `S3_SECRET_KEY`, the JWT keypair) are still at their insecure
development defaults. A misconfigured deployment should refuse to boot, not
serve traffic with a known signing key.

## What Phase 2 inherits

- `core/security.py`: `hash_password` / `verify_password` /
  `create_access_token` / `create_refresh_token` / `decode_token` — ready
  for real login, refresh rotation, and password-reset endpoints.
- `domain/users/*` + `SqlAlchemyUserRepository`: ready for a registration/
  login service layer to be built on top.
- `audit_logs` table: schema exists, write path is added once there are
  authenticated actions worth recording.
- `users.role`: the coarse actor type RBAC will layer role/permission
  tables on top of.
