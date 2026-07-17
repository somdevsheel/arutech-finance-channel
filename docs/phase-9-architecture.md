# Phase 9 — Admin Panel

Status: complete, covering every item `project.md` lists under Phase 9
(User Management, Role Management, Permission Management, Bank
Management, NBFC Management, Loan Product Management, Interest Rate
Management, Commission Management, Workflow Management, Notification
Templates, Email Templates, SMS Templates, WhatsApp Templates, CMS,
Settings, Audit Logs, System Logs, Feature Flags) with heavy
consolidation and one explicit deferral — see "Key design decisions"
and "Honest simplifications" below. This is by far the largest phase so
far: 6 backend subsystems, 8 admin frontend pages, and a migration
that removes real tech debt Phase 7 explicitly flagged.

## Scope

Phase 9 is "Admin Panel" — back-office catalog and configuration
management, distinct from the day-to-day operational work `leads.*`/
`customers.*`/`loans.*` cover. Consolidated into 6 subsystems:

1. **RBAC management** (User Management + Role Management + Permission
   Management) — an admin-facing layer over Phase 2's existing
   `users`/`roles`/`permissions`/`role_permissions`/`user_roles` tables.
2. **Lender management** (Bank Management + NBFC Management + Commission
   Management) — one new `Lender` entity.
3. **Loan Product management** (+ Interest Rate Management) — moves
   `LOAN_PRODUCTS` out of a hardcoded dict Phase 7 explicitly flagged as
   temporary, into a real admin-manageable table.
4. **Notification Templates** (Email + SMS + WhatsApp Templates) — one
   new `NotificationTemplate` entity, content only, no sending.
5. **CMS** — scoped to blog posts; the public `/blog` pages now read
   from the database instead of static content.
6. **Settings** (+ Feature Flags + Workflow Management) — one generic
   typed key-value store, with a real wired consumer.

**Audit Logs** needed no new backend — Phase 2 already built
`GET /api/v1/auth/audit-logs`; this phase's only work there is the first
admin frontend page for it. **System Logs** is explicitly deferred — see
"Honest simplifications."

## Layering

```
domain/
  lenders/          LenderEntity (type: bank|nbfc), LenderRepository.
  loans/
    product_entities.py, product_repository.py   LoanProductEntity —
      the database-backed replacement for the old products.py dict.
  notifications/     NotificationTemplateEntity (channel-discriminated),
                      NotificationTemplateRepository.
  cms/                BlogPostEntity + BlogSection, BlogPostRepository.
  settings/           SystemSettingEntity (typed key-value),
                       SystemSettingRepository, parse_bool_setting()
                       (the one shared parsing function both
                       SettingsService and LeadService use).
  rbac/               Extended: RoleEntity/PermissionEntity CRUD methods
                       added to the existing Phase 2 repository interface.
  users/              Extended: list_users/set_active/set_role added to
                       the existing Phase 1 repository interface.
services/
  lender_service.py, loan_product_service.py, notification_template_
  service.py, blog_post_service.py, settings_service.py,
  user_admin_service.py, rbac_service.py — one service per subsystem,
  each following the same create/list/get/update/audit-log pattern
  every prior phase established.
api/v1/endpoints/
  admin_users.py, admin_rbac.py, lenders.py, loan_products.py,
  notification_templates.py, cms.py, settings.py — plus two new routes
  added to the existing public.py for the CMS's public-facing half.
```

## Key design decisions

**Every "N similar things" item in project.md's Phase 9 list became one
mechanism with a discriminator, not N tables.** Bank + NBFC → one
`Lender` with a `type` enum. Email + SMS + WhatsApp Templates → one
`NotificationTemplate` with a `channel` enum. Settings + Feature Flags +
Workflow Management → one `SystemSetting` with a `value_type` enum. This
is the same consolidation pattern Phase 5 applied to follow-up
scheduling/tasks/reminders and Phase 6 applied to interaction channels —
by now, an established house style, not a new judgment call.

**All 10 new permissions are admin-only.** Unlike `leads.read`/
`customers.read`/`loans.read` (granted to `employee` too), nothing new
in this phase is — see `seed_data.py`'s comment. This is back-office
catalog/config management; there's no "employee who manages loan
products but isn't otherwise an admin" use case project.md asks for.
`roles.manage` alone gates all of Role + Permission Management (read
and write both) — there's no legitimate read-only audience for "which
permissions does this role have" distinct from who can also change it.

**Permission Management lets an admin assign *existing* permission
codes to roles — it does not let them invent new ones.**
`RbacRepository.list_permissions()`'s docstring explains why: a
permission code with no `require_permission(code)` call behind it in
actual endpoint code would do nothing. The fixed catalog is
code-defined; this phase makes it visible and assignable, not
open-ended.

**`UserAdminService.set_role` keeps the coarse `UserRole` column and the
fine-grained RBAC binding in sync automatically.** These are two
parallel systems since Phase 1/2 (`UserEntity.role` is the portal
selector; `roles`/`user_roles` drives permissions) that test helpers
(`_make_admin`, `_make_employee`) have always set together by hand. This
service formalizes that pairing: changing a user's role removes
whichever *system* role they currently hold and assigns the new one,
while leaving any custom (non-system) role grants Role Management
separately made untouched.

**Loan Product Management's real consumer migration.**
`LoanApplicationService` used to call `products.get_product(slug)` — a
synchronous dict lookup — at two call sites (`create_draft`'s bounds
validation, `_seed_document_checklist`). Both now call
`self._product_repo.get_by_slug(slug)`, a real DB query, via a new
`LoanProductRepository` constructor dependency. `domain/loans/
products.py` isn't deleted — its `LOAN_PRODUCTS`/`LoanProductLimits`
data lives on, repurposed as pure seed data: the Phase 9 migration
freezes a literal copy of it (never imports it — see the standing
"migrations never import a live module" rule), and `tests/conftest.py`
imports it directly to seed the same 7 products into the SQLite test
database, mirroring how `_seed_rbac` imports `seed_data.PERMISSIONS`.

**Settings gets exactly one real, wired consumer — not just CRUD for
its own sake.** `leads.auto_assignment_enabled` (seeded `true`) is
checked by `LeadService._auto_assign` before running Phase 5's
least-loaded assignment; turning it off via the Settings API leaves new
leads unassigned. `LeadService` depends on `SystemSettingRepository`
directly, not `SettingsService` — the same "services depend on
repositories, not other services" rule Phase 8's `DashboardService`
established, and also necessary to avoid a `deps.py` forward-reference
`NameError` (`get_settings_service` is defined after `get_lead_service`
in dependency-factory file order; the repository factory isn't).

**CMS is scoped to blog posts, not FAQs/job-openings/nav-links too.**
Blog is the one content type where "edit without a redeploy" is
unambiguously valuable and the content shape (title/excerpt/sections/
tags) doesn't leak into other systems. FAQs and job openings stay
static `content/*.ts` — smaller, more structured, and changed rarely
enough that a redeploy-on-change tradeoff is reasonable; migrating them
without a concrete need would be scope invention.

## Honest simplifications

**System Logs is explicitly not built.** A real searchable log viewer
needs a log-aggregation backend (Loki, ELK, CloudWatch Logs Insights)
that doesn't exist in this stack — Phase 1 already ships structured
JSON logs to stdout via structlog, and Prometheus/Grafana/OTel cover
metrics/traces. Building an in-app "System Logs" page backed by nothing
(no storage, no search, no retention) would be worse than not building
it — it would look like observability without providing any. If a log
aggregation service is added to `docker-compose.yml` in a later phase,
a real admin log-viewer page can point at it then.

**Loan Product Management's frontend migration stops at the backend.**
`LoanApplicationService` now reads products from the database — the
real tech debt Phase 7 flagged. The public marketing site's `/loans`
and `/loans/[slug]` pages still read `content/loan-products.ts` (static,
statelessly SSG'd), left untouched on purpose: migrating them would
mean either losing build-time static generation for the product catalog
pages or adding a second live-fetch pattern for content that changes
far less often than blog posts, for marketing copy (tagline, features,
eligibility highlights) the database model doesn't even carry — it only
has the bounds/documents the backend actually validates against. CMS
(blog) demonstrates the "live-fetch, admin-editable" pattern for when
loan product marketing pages genuinely need it.

**Bank Routing remains internal employee assignment, still not
multi-lender routing** — unchanged from Phase 7's own deferral.
`Lender` now exists, satisfying the immediate dependency Phase 7 named,
but nothing yet links a specific `LoanApplication` to a specific
`Lender`: no `lender_id` field, no routing UI. That link needs a real
routing workflow, which needs Phase 11's Partner Bank Portal to receive
what gets routed — adding a dangling foreign key now, with nothing
using it, would be schema speculation. `COMMISSION_RATE_PERCENT` (Phase
7's flat 1% constant) is unchanged for the same reason: `Lender.
commission_rate_percent` exists and is manageable, but disbursement
doesn't consume it yet, since nothing assigns a lender to an
application to read the rate *from*.

## Frontend integration

Eight new pages under `app/admin/`, following the same pattern Phase 8
established (plain, non-route-group folders — `/admin/*` needs its own
URL segment):

```
app/admin/
  users/page.tsx                    List + activate/deactivate + role change
  roles/page.tsx, roles/[id]/page.tsx    List/create/delete + permission grant/revoke
  lenders/page.tsx                  List/create + activate/deactivate
  loan-products/page.tsx            List/create + activate/deactivate
  notification-templates/page.tsx   List/create + activate/deactivate
  cms/blog-posts/page.tsx           List/create + publish/unpublish/delete
  settings/page.tsx                 List + per-row update
  audit-logs/page.tsx               Read-only (reuses Phase 2's endpoint)
lib/admin/
  session.ts    Extended with ~12 more read functions, all going through
                 two new generic helpers (fetchAdminList/fetchAdminOne)
                 instead of copy-pasting the try/catch 15 more times.
  actions.ts     ~20 Server Actions — one per mutation across all 6
                  subsystems.
lib/cms/session.ts   Public, unauthenticated reads (listPublishedBlogPosts,
                      getPublishedBlogPost) — a different trust boundary
                      from lib/admin/session.ts, backing the marketing
                      site's /blog pages.
components/admin/
  admin-create-form.tsx    A reusable client-side wrapper every "New X"
                            form uses — see "Bugs found" below for why
                            it exists.
  toggle-active-button.tsx, user-role-form.tsx, delete-role-button.tsx,
  revoke-permission-button.tsx, blog-post-actions.tsx, setting-row.tsx
```

**No react-hook-form/zod for admin CRUD forms.** Every prior phase's
customer/public-facing form (loan apply, EMI calculator, contact form)
uses react-hook-form + zod for real-time validation UX. Phase 9's admin
forms are plain `<form>` elements reading `FormData` directly — internal
tooling doesn't carry the same UX bar as a conversion-critical public
flow, and the backend re-validates every field regardless (a bad bound,
a duplicate slug, an invalid boolean all come back as a real error from
the service layer either way).

**The `/blog` pages moved off `content/blog-posts.ts` entirely** — the
file was deleted, not left as a fallback, once nothing referenced it.
`lib/cms/session.ts` provides `listPublishedBlogPosts`/
`getPublishedBlogPost` (public, unauthenticated, distinct trust boundary
from `lib/admin/session.ts`), and `sitemap.ts` now awaits the same call
instead of importing the static array.

### Bugs found integrating the frontend

**Server Actions used directly as `<form action={...}>` must return
`void`, not a result object.** Every mutation in `lib/admin/actions.ts`
returns `ActionResult` (so it *can* report a specific error message) —
but Next.js's form-action typing requires `void | Promise<void>` for a
function passed straight to a form's `action` prop, since the framework
has no channel to surface a returned value from that binding. `tsc`
caught this immediately (6 pages, all with the identical error) — not a
runtime bug, a real type error, but one that would've been easy to
"fix" by just discarding error messages instead of building the actual
fix: `components/admin/admin-create-form.tsx`, a small client wrapper
that intercepts submit, calls the action inside a transition, and
toasts the error if `result.ok` is false. Every "New X" form in this
phase uses it instead of a bare `<form action={serverAction}>`.

**Blog pages needing a live API broke the production build with no
API running.** `generateStaticParams` in `blog/[slug]/page.tsx` and the
`/blog` index page itself both now call `listPublishedBlogPosts()` —
previously a static import that could never fail. In this sandboxed
build environment (no `docker compose` backend running, `api` hostname
unresolvable), that turned into a hard `next build` failure:
`getaddrinfo EAI_AGAIN api`, first on `/blog/[slug]`'s
`generateStaticParams`, then again on `/blog` itself once the first was
fixed. This is a real architectural risk beyond just this sandbox — any
CI/Docker build stage that builds the `web` image before `api` is
reachable would hit the identical failure. Fixed by making
`listPublishedBlogPosts()` itself absorb any fetch failure into an
empty list (`lib/cms/session.ts`) rather than throwing: a public blog
listing quietly showing zero posts during a build-time outage is a far
safer degradation than failing the entire production build over it.
`getPublishedBlogPost` (single slug) deliberately does *not* get this
same blanket catch — silently turning "the API is unreachable" into
"this post doesn't exist" (a 404) would misrepresent real content as
missing, which is worse than a loud failure for that specific case.
Caught only by actually running `next build`, the same "verify by
running it, not just typecheck/lint" lesson Phase 7's route-collision
bug and Phase 8's `EXTRACT(ISODOW)` bug both taught — three phases
running now where the thing that actually breaks isn't caught by
static analysis.

## Database schema (migration `a9e3b9b15ff5`)

Five new tables — `lenders`, `loan_products`, `notification_templates`,
`blog_posts`, `system_settings` — generated via `alembic revision
--autogenerate` against a scratch Postgres container (not hand-written,
given the volume) and then hand-extended with seed-data logic: 10 new
permissions (admin-only), 7 loan products (frozen copy of
`products.py`'s existing catalog), 3 blog posts (frozen copy of the
existing `content/blog-posts.ts`, seeded already-published at their
original publish dates so the public site doesn't lose content when the
frontend switches over), and 1 system setting
(`leads.auto_assignment_enabled = true`).

**Bug caught by verifying against real Postgres, not just `ruff`/
`mypy`:** the three new `StrEnum`-backed columns (`Lender.type`,
`NotificationTemplate.channel`, `SystemSetting.value_type`) were first
written as plain `Enum(SomeStrEnum, name=...)`, which defaults to
persisting the Python enum *member name* (`"BANK"`, `"EMAIL"`,
`"BOOLEAN"` — uppercase) rather than its `.value`. Every existing enum
column in this codebase (`LoanApplicationStatus`, `CustomerSegment`,
etc.) instead passes `values_callable=lambda cls: [m.value for m in
cls]` to force lowercase storage matching the domain entities — an
established, consistent convention across `models/loans.py` and
`models/crm.py` that these three new files simply missed. Neither
`ruff` nor `mypy` catches this (there's nothing type-checkable about a
SQL enum's on-the-wire representation); it only surfaced as a real
`InvalidTextRepresentationError` when applying the migration's own seed
data (`value_type='boolean'`) against the enum type the same migration
had just created (`'STRING', 'BOOLEAN', 'NUMBER'`) on a live scratch
Postgres container. Fixed by adding the missing `values_callable` to
all three models and regenerating the migration's enum literals to
lowercase, then re-verified with a full up → down → up cycle.

## Security

All 10 new permissions are admin-only (see "Key design decisions").
`GET /api/v1/public/blog-posts*` is the one genuinely public,
unauthenticated surface this phase adds — mirroring Phase 3's
`/api/v1/public/contact` and Phase 7's dual-access pattern, it only ever
returns `is_published=True` posts; a draft slug 404s for an
unauthenticated visitor the same way Phase 7's `get_own` 404s (not
403s) on someone else's application, so a guessed slug can't confirm a
draft's existence. Every mutation across all 6 subsystems is
audit-logged with actor and metadata, extending the "who did what and
when" guarantee every phase since Phase 2 has carried forward.
