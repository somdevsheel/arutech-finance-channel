# apps/api — Arutech Finance Platform backend

FastAPI, async SQLAlchemy 2.0 + Alembic, Celery, structured logging (JSON via
structlog), OpenTelemetry, Prometheus metrics. Dependency-managed with
[uv](https://docs.astral.sh/uv/).

## Structure (clean architecture / DDD)

```
src/arutech_api/
  api/v1/            FastAPI routers + endpoint handlers. HTTP only.
  core/              Config, security (hashing + JWT), logging, the DB
                      engine/session, the Redis client, telemetry,
                      middleware, exception -> HTTP mapping, rate limiting.
  domain/            Entities + repository *interfaces*. No framework
                      imports — domain/users/entities.py doesn't know
                      SQLAlchemy or FastAPI exist.
  infrastructure/    SQLAlchemy models + repository *implementations*.
  services/          Use-case orchestration (empty in Phase 1; Phase 2
                      adds auth_service.py and friends).
  main.py            App factory + ASGI app instance.
  worker.py          Celery app + task registry.
alembic/             Migrations. env.py always reads the DB URL from
                      Settings, never from alembic.ini.
tests/
  unit/              No I/O — security, worker task logic.
  integration/       Hits a real (if in-memory SQLite) DB via the
                      repository, and the HTTP app via httpx.
scripts/
  generate_jwt_keypair.py   Dev-only RS256 keypair generator.
```

See `../../docs/phase-1-architecture.md` for why it's laid out this way.

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

## API surface (Phase 1)

- `GET /api/v1/health` — liveness, no dependency checks.
- `GET /api/v1/health/ready` — readiness; checks Postgres + Redis, returns
  503 if either is unreachable.
- `GET /metrics` — Prometheus scrape endpoint (excluded from the OpenAPI
  schema).
- `GET /docs`, `/redoc` — OpenAPI UI (disabled when `ENVIRONMENT=production`).

Auth endpoints (register/login/refresh/OTP/password-reset) are Phase 2 —
`core/security.py` already has the primitives they'll be built on.
