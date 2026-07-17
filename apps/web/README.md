# apps/web — Arutech Finance Platform frontend

Next.js 16 (App Router), TypeScript, Tailwind v4, shadcn/ui, TanStack Query,
React Hook Form + Zod, Motion. Built via `create-next-app` and extended for
this project — see [`node_modules/next/dist/docs`](node_modules/next/dist/docs)
for Next.js 16 conventions if something looks unfamiliar (notably: Middleware
is now `proxy.ts`, and `fetch` is uncached by default unless wrapped in
`"use cache"`).

**shadcn note**: this project's shadcn preset (`base-nova`) is Base UI-flavored,
not Radix. Polymorphic components use a `render` prop, not `asChild` —
`<Button render={<Link href="/x" />}>Text</Button>`, never `<Button asChild>
<Link>Text</Link></Button>`. The `form` registry component is an empty stub in
this version; forms are built directly with `react-hook-form` +
Label/Input/Textarea instead.

## Structure

```
src/
  app/
    (marketing)/     Public site route group — its own header/footer layout.
                       Maps to / (route groups don't affect the URL). Owns
                       /loans and /loans/[slug] (the public product catalog)
                       — see the (portal)/applications/ note below for why
                       the customer-facing loan *applications* area is named
                       differently.
    (auth)/           login, register, forgot-password — public, redirect
                       away if already authenticated (Phase 4).
    (portal)/         Signed-in customer portal — auth-gated by proxy.ts.
      dashboard/       Overview: loan application count, profile, sessions.
      applications/    List, apply, and per-application detail/status/
                        document-checklist pages (Phase 7). Named
                        `applications`, not `loans`, specifically to avoid
                        colliding with (marketing)'s `/loans` — Next.js
                        route groups don't add a URL segment, so both
                        route groups share one flat URL space.
      profile/, sessions/    Phase 4.
    admin/            Executive dashboard + admin panel — a plain folder,
                       not a `(admin)` route group, since `/admin/*`
                       genuinely needs its own URL segment (Phase 8).
                       layout.tsx redirects non-admins away.
      dashboard/       KPIs, lead funnel, activity heatmap, alerts,
                        system health (Phase 8).
      users/, roles/, roles/[id]/, lenders/, loan-products/,
      notification-templates/, cms/blog-posts/, settings/,
      audit-logs/      Phase 9's Admin Panel — one page per subsystem;
                        see components/admin/ below for the shared
                        pieces every list page uses.
    status/          Relocated Phase 1 system-status page (noindex,
                       disallowed in robots.ts — discloses internal service
                       info, not meant for public visitors).
    sitemap.ts, robots.ts   Next.js file-convention SEO endpoints.
    providers.tsx    Wires TanStack Query + the toaster around the tree.
  proxy.ts            Gates (portal)/* and admin/* routes and silently
                       refreshes the access token — see
                       docs/phase-4-architecture.md. Login redirects to
                       /admin/dashboard or /dashboard based on role
                       (login-form.tsx's resolveRedirect()), unless an
                       explicit ?next= is present (Phase 8).
  components/
    ui/              shadcn/ui primitives (generated, don't hand-edit — re-run
                       `pnpm dlx shadcn@latest add <component>` instead)
    marketing/        Public-site building blocks: section headings,
                       calculator forms, contact form, legal-page renderer
    auth/             Login/register/forgot-password forms (Phase 4).
    portal/           Portal shell (header, sign-out) + loan application
                       card/status-badge/apply-form/document-checklist
                       (Phase 7).
    admin/            admin-header.tsx, kpi-card.tsx, lead-funnel-chart.tsx,
                       activity-heatmap.tsx, alerts-panel.tsx,
                       system-health-panel.tsx, dashboard-auto-refresh.tsx
                       (client component; polls via router.refresh() —
                       see docs/phase-8-architecture.md's "Real-Time
                       Monitoring" note) (Phase 8). admin-create-form.tsx
                       (every "New X" form's shared wrapper — see
                       docs/phase-9-architecture.md's "Bugs found" for why
                       a bare `<form action={serverAction}>` doesn't
                       typecheck), toggle-active-button.tsx,
                       user-role-form.tsx, delete-role-button.tsx,
                       revoke-permission-button.tsx, blog-post-actions.tsx,
                       setting-row.tsx (Phase 9).
    analytics/        google-analytics.tsx (GA4, no-op without an env var)
    site-header.tsx, site-footer.tsx
  content/           Static typed content: loan-products.ts, faqs.ts,
                       job-openings.ts, nav-links.ts. blog-posts.ts was
                       deleted in Phase 9 — the /blog pages now read from
                       the database via lib/cms/session.ts; loan-products.ts
                       stays static on purpose (see
                       docs/phase-9-architecture.md's "Honest
                       simplifications" — the backend catalog moved to a
                       real table, the public marketing pages didn't).
  hooks/             TanStack Query hooks (use-platform-health.ts)
  lib/
    api-client.ts     Typed fetch wrapper
    env.ts            Zod-validated env vars
    loan-calculations.ts   EMI + eligibility formulas (pure, unit-tested) —
                            ported line-for-line into the backend's
                            domain/loans/calculations.py in Phase 7 so both
                            sides agree on the same numbers.
    auth/              constants.ts (session cookie config), schemas.ts,
                        session.ts (read-only Server Component fetches),
                        actions.ts (Server Actions: login/register/OTP/
                        password reset/logout/session revoke) (Phase 4).
    loans/             Same session.ts/actions.ts/schemas.ts split as
                        lib/auth/, for loan applications (Phase 7).
    admin/             session.ts (Phase 8's five dashboard reads, plus
                        ~12 more for Phase 9's subsystems — both go
                        through two generic helpers, fetchAdminList/
                        fetchAdminOne, instead of repeating the same
                        try/catch), actions.ts (Phase 9 only — ~20 Server
                        Actions, one per mutation across all 6
                        subsystems; dashboard stayed read-only in Phase 8
                        so it never needed one).
    cms/               session.ts — public, unauthenticated reads
                        (listPublishedBlogPosts, getPublishedBlogPost),
                        a different trust boundary from lib/admin/
                        session.ts. Backs the marketing site's /blog
                        pages (Phase 9).
    format.ts, structured-data.ts, analytics.ts
  types/              auth.ts, loans.ts, dashboard.ts, admin.ts — API
                       response shapes.
  tests/              Vitest setup (jest-dom matchers)
```

Colocated `*.test.tsx` / `*.test.ts` files sit next to what they test.

## Commands

```bash
pnpm dev              # dev server (Turbopack)
pnpm build            # production build (standalone output, for Docker)
pnpm lint             # eslint (core-web-vitals + TypeScript rules)
pnpm typecheck        # tsc --noEmit
pnpm test             # vitest run
pnpm test:watch
pnpm test:coverage
```

## Environment variables

See `.env.example`. `NEXT_PUBLIC_*` vars are bundled into the client bundle
at **build time** — never put a secret there, and note that a
`docker-compose.yml` `environment:` override has no effect on them (the
value is already baked into the compiled bundle); use a Docker build `arg`
instead, as `NEXT_PUBLIC_SITE_URL` does. `API_INTERNAL_URL` is server-only,
used by server components/route handlers to reach the API over the Docker
network (`http://api:8000`); it falls back to `NEXT_PUBLIC_API_URL` when
unset, so local dev without Docker works with just the public URL.
`NEXT_PUBLIC_GA_MEASUREMENT_ID` is unset by default — analytics is a no-op
until it's a real GA4 ID.

## What's here vs. what's coming

Phases 1–9 ship the app shell, the public marketing site (home, about,
contact, careers, blog — database-backed via a public CMS API since
Phase 9, FAQs, legal pages, loan products, EMI/eligibility calculators,
SEO, analytics), a signed-in customer portal (auth, Phase 4; loan
applications — browse products, apply, track status through the full
origination pipeline, submit checklist documents, Phase 7), and an
admin-only area (`/admin/*`, role-gated): an executive dashboard
(business KPIs, lead funnel, activity heatmap, alerts, system health,
Phase 8) plus a full admin panel (user/role/permission management,
lender and loan product catalogs, notification templates, CMS, settings/
feature flags, audit logs, Phase 9). Employee and partner portals
(Phases 10–11) land as their own top-level folders in this same
workspace when their phases come up, the same way `admin/` did.
