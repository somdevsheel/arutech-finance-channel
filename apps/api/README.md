# apps/api — Arutech Finance Platform backend

FastAPI, async SQLAlchemy 2.0 + Alembic, Celery, structured logging (JSON via
structlog), OpenTelemetry, Prometheus metrics. Dependency-managed with
[uv](https://docs.astral.sh/uv/).

## Structure (clean architecture / DDD)

```
src/arutech_api/
  api/
    deps.py          get_current_user, require_permission(code), and every
                      repository/service Depends() provider.
    v1/endpoints/    FastAPI routers + endpoint handlers. HTTP only.
    v1/schemas/      Pydantic request/response DTOs (not under domain/ —
                      see docs/phase-2-architecture.md).
  core/              Config, security (hashing + JWT + OTP), logging, the
                      DB engine/session, the Redis client, telemetry,
                      middleware, exception -> HTTP mapping, rate limiting.
  domain/            Entities + repository *interfaces*. No framework
                      imports — nothing under domain/ knows SQLAlchemy,
                      FastAPI, or Pydantic exist.
    auth/            RefreshToken/Otp entities + repository interfaces +
                      OtpDeliveryPort (Phase 13 adds real SMS/email
                      adapters against this same interface).
    rbac/            Role/Permission entities + repository interface.
    audit/           AuditLog entity + repository interface (list_for_entity
                      backs Phase 5's lead activity/tracking view).
    users/           User entity + repository interface (Phase 1).
    contact/         ContactSubmission entity + repository interface (Phase 3).
    leads/           Lead + LeadTask entities, LeadStatus pipeline
                      (ALLOWED_TRANSITIONS state machine), LeadSource,
                      repository interfaces, scoring.py (a pure,
                      deterministic score_lead() function) (Phase 5).
  infrastructure/    SQLAlchemy models + repository *implementations*, and
                      notifications/log_otp_delivery.py (the Phase 2
                      OtpDeliveryPort adapter — logs the code).
  services/          Use-case orchestration: auth_service.py (register,
                      login, OTP, refresh rotation, password reset,
                      sessions), audit_service.py, contact_service.py
                      (public contact-form submissions, with honeypot
                      spam filtering — now also creates a lead via
                      lead_service.py on every real submission),
                      lead_service.py (duplicate detection, scoring,
                      auto-assignment, pipeline transitions, import/export,
                      analytics, all audit-logged), and
                      lead_task_service.py (follow-up tasks/reminders).
  main.py            App factory + ASGI app instance.
  worker.py          Celery app + task registry.
alembic/             Migrations. env.py always reads the DB URL from
                      Settings, never from alembic.ini.
tests/
  unit/              No I/O — security/OTP hashing, worker task logic,
                      lead scoring/transition rules.
  integration/       Hits a real (if in-memory SQLite) DB via the
                      repository, and the HTTP app via httpx.
scripts/
  generate_jwt_keypair.py   Dev-only RS256 keypair generator.
```

See `../../docs/phase-1-architecture.md`, `../../docs/phase-2-architecture.md`,
`../../docs/phase-3-architecture.md`, `../../docs/phase-4-architecture.md`,
and `../../docs/phase-5-architecture.md` for why it's laid out this way.

## Commands

```bash
uv sync                        # install deps (+ dev group)
uv run uvicorn arutech_api.main:app --reload
uv run ruff check .            # lint
uv run ruff format .           # format
uv run mypy                    # strict type check
uv run pytest                  # unit + integration tests, with coverage
uv run alembic revision --autogenerate -m "..."
uv run alembic upgrade head
uv run python scripts/generate_jwt_keypair.py >> .env
```

## Environment variables

See `.env.example`. `get_settings()` (in `core/config.py`) will raise at
import time — not at first request — if `ENVIRONMENT` is `staging` or
`production` and secrets are still at their insecure development defaults,
or the JWT keypair is unset.

## Testing without Docker

Integration tests use an isolated in-memory SQLite database per test (see
`tests/conftest.py`), so `uv run pytest` needs no running Postgres/Redis.
The one exception is genuinely exercising `/api/v1/health/ready` against
real infrastructure, which needs `docker compose up -d postgres redis`
first — the unit-level readiness tests instead monkeypatch the two
connectivity checks to test the endpoint's status-code/aggregation logic
deterministically.

## API surface

**Phase 1**

- `GET /api/v1/health` — liveness, no dependency checks.
- `GET /api/v1/health/ready` — readiness; checks Postgres + Redis, returns
  503 if either is unreachable.
- `GET /metrics` — Prometheus scrape endpoint (excluded from the OpenAPI
  schema).
- `GET /docs`, `/redoc` — OpenAPI UI (disabled when `ENVIRONMENT=production`).

**Phase 2** — all under `/api/v1/auth`

- `POST /register`, `POST /login`
- `POST /otp/request`, `POST /otp/verify`
- `POST /refresh` (rotates the token; reusing an already-rotated one
  revokes every session), `POST /logout`, `POST /logout-all`
- `POST /password-reset/request`, `POST /password-reset/confirm`
- `GET /me`
- `GET /sessions`, `DELETE /sessions/{id}`
- `GET /audit-logs` — requires the `audit_logs.read` permission (seeded for
  the `admin` and `employee` roles; see `infrastructure/database/seed_data.py`)

**Phase 3**

- `POST /api/v1/public/contact` — public, rate-limited (5/min), backs the
  website's Contact page. Silently no-ops (200, nothing stored) if the
  hidden honeypot field is filled in. As of Phase 5, a real submission also
  creates (or bumps a duplicate of) a lead.

**Phase 5** — all under `/api/v1/leads`, requiring `leads.read`
(GET routes) or `leads.manage` (POST routes)

- `GET ""` — list leads, filterable by `status`/`assigned_to`, sorted by
  score then recency.
- `GET /export` — same filters, streamed as CSV.
- `POST /import` — bulk-create leads from a JSON array; goes through the
  same duplicate-detection/scoring/auto-assignment pipeline as a contact
  submission.
- `GET /analytics/summary` — totals, counts by status/source, average
  score, conversion rate.
- `GET /tasks/mine` — the caller's own follow-up task queue.
- `POST /tasks/{task_id}/complete`
- `GET /{lead_id}`
- `POST /{lead_id}/status` — moves a lead through the pipeline; rejects
  illegal transitions (409) per `domain/leads/entities.ALLOWED_TRANSITIONS`.
- `POST /{lead_id}/assign` — assigns to an employee/admin user; rejects
  customers/partners as assignees (409) and unknown user IDs (404).
- `GET /{lead_id}/activity` — that lead's audit-log timeline.
- `GET /{lead_id}/tasks`, `POST /{lead_id}/tasks` — follow-up
  scheduling/reminders, assigned to an employee/admin.
