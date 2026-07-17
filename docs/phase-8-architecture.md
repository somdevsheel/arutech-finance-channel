# Phase 8 — Admin Dashboard

Status: complete, covering every item `project.md` lists under Phase 8
(Executive Dashboard, Business KPIs [Revenue, Commission, Employees,
Customers, Loans, Approvals], Lead Funnel, Conversion Analytics,
Heatmaps, Real-Time Monitoring, Alerts, System Health) with a few
explicitly-scoped simplifications — see "Honest simplifications" below.
Builds on Phase 5's Lead analytics, Phase 6's Customer analytics, and
Phase 7's Loan analytics — this phase adds no new source-of-truth data,
it composes and presents what those three phases already track.

## Scope

A read-only executive dashboard: a handful of business KPIs, a lead
pipeline funnel, a temporal activity heatmap, a small set of
deterministic operational alerts, and a system-health panel — all
admin-only, all computed at read time from existing tables. Like Phase 7,
this phase touches both `apps/api` and `apps/web`: a dashboard is
meaningless without somewhere to look at it, so this is the first phase
to add a genuinely new frontend area (`/admin/*`) rather than extend the
existing customer portal.

## Layering

```
domain/dashboard/
  entities.py    ExecutiveKpis, FunnelStageEntry + LeadFunnel,
                 HeatmapCell + ActivityHeatmap, AlertSeverity + Alert,
                 SystemHealthSummary — all read-models; none of them
                 back a database table.
  alerts.py      evaluate_alerts() — a pure function (metrics in, alerts
                 out), unit-tested directly without a DB, the same
                 pattern calculations.py established in Phase 7.
services/
  dashboard_service.py   DashboardService — composes LeadRepository,
                          CustomerRepository, LoanApplicationRepository,
                          and UserRepository directly (not their
                          services; see "Key design decisions").
api/v1/schemas/dashboard.py, api/v1/endpoints/dashboard.py
  /api/v1/admin/dashboard/{kpis,lead-funnel,activity-heatmap,alerts,
  system-health} — five GET routes, all gated by a single new
  `dashboard.read` permission.
```

No new SQLAlchemy models and no new tables: Phase 8's migration
(`855cc489f8bf`) seeds one permission and nothing else.

## Key design decisions

**`DashboardService` depends on repositories directly, not on
`LeadService`/`CustomerService`/`LoanApplicationService`.** Those
services orchestrate business *transactions* (state machines, audit
logging, validation). This phase does none of that — it's pure
composition of existing read queries (`get_analytics_summary()` on three
different repositories, plus two new narrow query methods). Depending on
the services would add nothing but an extra indirection layer and a
false impression that the dashboard *does* something, when it only
*looks*.

**Two new repository methods, not a new "analytics" repository.**
`LeadRepository.get_hourly_activity_counts()` and
`LoanApplicationRepository.get_hourly_activity_counts()` are narrow
additions to repositories that already exist, the same way Phase 7 added
`LoanDocumentRepository` alongside `LoanApplicationRepository` rather
than inventing a shared "reporting" repository that would blur
ownership. `UserRepository.count_by_role()` is a `COUNT(*)` sibling of
the `list_by_role()` Phase 5 already added.

**`EXTRACT(DOW ...)`, not `EXTRACT(ISODOW ...)`.** Postgres supports
both, but SQLite (which the test suite's `db_session` fixture uses —
see `seed_data.py`'s docstring) has no ISODOW equivalent in its
`extract_map`; a first pass using ISODOW passed `ruff`/`mypy` and only
failed at integration-test time with a SQLite `KeyError`. DOW is the one
day-of-week field both dialects support, and — conveniently — with an
identical `0=Sunday..6=Saturday` numbering on both, verified directly
against a live Postgres container (`EXTRACT(DOW FROM '2026-07-17
10:00')` → `5`, a Friday) as well as SQLite's `strftime('%w', ...)`. See
"Bugs found" below.

**"Pending approval" covers `SUBMITTED` and `UNDER_REVIEW`, not just
`UNDER_REVIEW`.** The first draft only counted `UNDER_REVIEW`
(assigned, being worked) and undercounted: an application sitting in
`SUBMITTED` (not yet assigned to anyone) is arguably *more* urgently
"pending approval," not less. `_pending_approval_count()` in
`dashboard_service.py` sums both statuses; both the `loans_pending_approval`
KPI and the alert threshold use it, so they can't drift apart.

**A small, deterministic, threshold-based `Alert` generator — not a
rules engine.** `evaluate_alerts()` checks three fixed conditions
(pending-approval backlog, customers without a relationship manager,
new-lead backlog) against named constants
(`PENDING_APPROVAL_WARNING_THRESHOLD`, etc.), the same "honest
heuristic, not a fabricated system" choice Phase 7's `assess_credit`
made. A configurable alerting/notification system with delivery
channels is Phase 13's "Notification Center" territory.

**`dashboard.read` is a single, admin-only permission — not split into
`dashboard.kpis.read` / `dashboard.alerts.read` / etc.** All five
endpoints show different facets of the same executive-level picture;
splitting them into separately grantable permissions would imply a
partial-visibility use case ("this employee should see the funnel but
not the alerts") that project.md never asks for. Unlike every `*.read`
permission before it, it is **not** granted to `employee` — see
`seed_data.py`'s comment. project.md scopes this phase to "Admin
Dashboard" specifically, with "Employee Portal" landing separately in
Phase 10.

## Honest simplifications

**The Lead Funnel is a current-status snapshot, not a historical cohort
funnel.** "Of leads created in January, how many *ever* reached
QUALIFIED" needs stage-transition timestamps as a dedicated fact table,
which doesn't exist — `AuditLog` records transitions, but reconstructing
cohort funnels from its free-form JSON metadata would be fragile
infrastructure this phase doesn't need to build. `LeadFunnel` instead
reports how many leads are *currently* at each pipeline stage, in
pipeline order, which is what Phase 5's `LeadAnalyticsSummary.by_status`
already computed — see `domain/dashboard/entities.py`'s `LeadFunnel`
docstring.

**The Activity Heatmap is temporal (day-of-week x hour-of-day), not
geographic.** A geographic heatmap was the first idea and was dropped on
inspection: neither `LeadEntity`, `CustomerProfileEntity`, nor
`UserEntity` has a city/state/region field anywhere in the system.
Building one would mean inventing location data that isn't collected,
not visualizing something real. The temporal heatmap uses timestamp data
(`created_at`) that already exists on both `leads` and
`loan_applications`.

**Real-Time Monitoring is polling, not push.** The dashboard page
mounts a client component (`DashboardAutoRefresh`) that calls
`router.refresh()` every 30 seconds — the same interval
`use-platform-health.ts` already polls at — re-running the page's
Server Component data fetches. There's no WebSocket/SSE layer; standing
one up would be new infrastructure this project doesn't otherwise need,
for a dashboard where a 30-second staleness window is a non-issue.

**System Health wraps the existing `/health/ready` checks, not a new
monitoring stack.** `check_database_connection()` /
`check_redis_connection()` (Phase 1) are called directly from
`DashboardService.get_system_health()` — this phase adds a dashboard
panel over data that already existed, not a second parallel
health-check mechanism. Prometheus/Grafana (also Phase 1) remain the
real observability stack; this panel is a convenience view for an admin
already looking at the dashboard.

## Frontend integration

A new top-level `app/admin/` folder — deliberately **not** a
parenthesized route group like `(marketing)`/`(portal)`. Those two share
a flat URL namespace on purpose (route groups don't add a URL segment);
`/admin/*` genuinely needs its own segment, so it's a plain folder with
its own `layout.tsx`, matching how `/api/v1/admin/dashboard/*` is
prefixed on the backend.

```
lib/admin/
  session.ts   getExecutiveKpis, getLeadFunnel, getActivityHeatmap,
               getAlerts, getSystemHealth — mirrors lib/loans/session.ts's
               read-only pattern; 401 *and* 403 both fold to an empty
               result (admin/layout.tsx is the real gate; this is a
               defensive second line, same reasoning as
               (portal)/layout.tsx's docstring).
app/admin/
  layout.tsx          Redirects unauthenticated visitors to /login, and
                       non-admin authenticated users to /dashboard.
  dashboard/page.tsx   Fetches all five endpoints in parallel
                        (Promise.all) and renders KPI cards, the funnel
                        chart, the heatmap, alerts, and system health.
components/admin/
  kpi-card.tsx, lead-funnel-chart.tsx, activity-heatmap.tsx,
  alerts-panel.tsx, system-health-panel.tsx, admin-header.tsx,
  dashboard-auto-refresh.tsx
```

**No new chart library.** The funnel (horizontal bars) and heatmap (a
7x24 grid of opacity-scaled cells) are hand-built with Tailwind
utilities and inline `style` for data-driven values (bar width, cell
opacity) rather than adding Recharts or similar — both visualizations
are simple enough that a dependency would be pure overhead, and it keeps
`package.json`'s dependency list exactly as it was through Phase 7.

**Login redirects admins to `/admin/dashboard`, not `/dashboard`, absent
an explicit `?next=`.** `login-form.tsx`'s `resolveRedirect()` checks the
just-authenticated user's role: an explicit `next` (e.g. proxy.ts
bouncing someone back to a specific page) always wins, but the *default*
target now depends on role, where before Phase 8 every login defaulted
to the customer portal.

### Bugs found integrating the frontend

**`/applications` was missing from `proxy.ts`'s `PORTAL_PREFIXES` /
matcher — a Phase 7 gap, found while adding `/admin`.** `proxy.ts` is
the only place that silently refreshes an expiring access token (see its
own docstring: Server Components are read-only and can't set cookies).
Every portal route needs to be in its matcher for that refresh to cover
it; Phase 7 added the `/applications` routes but never added the prefix,
so a customer whose access token expired while browsing their loan
applications would have been silently logged out instead of silently
refreshed — the exact failure mode `proxy.ts` exists to prevent, just
not exercised by any Phase 7 test (none of them ran long enough for a
15-minute token to actually expire). Fixed alongside adding `/admin` to
the same list, and caught only by rereading `proxy.ts` in full while
extending it, not by any automated check — a reminder that a matcher
list is exactly the kind of thing that silently rots when a phase adds a
route and forgets a step.

**`EXTRACT(ISODOW ...)` passed every backend check except the one that
mattered.** Covered above under "Key design decisions" — flagged here
too because of *how* it surfaced: `ruff` and `mypy` were both clean
(there's nothing type-checkable about a SQL function name string), and
it only broke at `pytest` time with a SQLite `KeyError` three layers deep
in SQLAlchemy's compiler. Same lesson Phase 7's route collision taught
about `next build`: some categories of bug only show up when the code
actually runs against the real (or in this case, test) environment.

## Database schema (migration `855cc489f8bf`)

No new tables. One new permission: `dashboard.read` ("View the
executive dashboard: KPIs, funnel, heatmap, alerts, system health"),
granted to `admin` only — following the frozen-migration-constant
pattern `0701461178f7` (Phase 5) established, now used identically by
every migration since.

## Security

All five `/api/v1/admin/dashboard/*` routes require `dashboard.read`,
re-checked from the database per request like every permission before
it. Unlike `leads.read`/`customers.read`/`loans.read`, it is not granted
to `employee` — this is exec-level aggregate data across the whole
business, a different audience than the per-record permissions
employees already have for their own work queues. The frontend gate
(`app/admin/layout.tsx`, checking `role === "admin"`) is a second,
independent check in front of the same backend enforcement — consistent
with `(portal)/layout.tsx` re-verifying auth instead of trusting
`proxy.ts` alone.
