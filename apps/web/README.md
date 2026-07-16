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
                       Maps to / (route groups don't affect the URL).
    status/          Relocated Phase 1 system-status page (noindex,
                       disallowed in robots.ts — discloses internal service
                       info, not meant for public visitors).
    sitemap.ts, robots.ts   Next.js file-convention SEO endpoints.
    providers.tsx    Wires TanStack Query + the toaster around the tree.
  components/
    ui/              shadcn/ui primitives (generated, don't hand-edit — re-run
                       `pnpm dlx shadcn@latest add <component>` instead)
    marketing/        Public-site building blocks: section headings,
                       calculator forms, contact form, legal-page renderer
    analytics/        google-analytics.tsx (GA4, no-op without an env var)
    site-header.tsx, site-footer.tsx
  content/           Static typed content: loan-products.ts, blog-posts.ts,
                       faqs.ts, job-openings.ts, nav-links.ts. Phase 9's CMS
                       will eventually replace this as the data source.
  hooks/             TanStack Query hooks (use-platform-health.ts)
  lib/
    api-client.ts     Typed fetch wrapper
    env.ts            Zod-validated env vars
    loan-calculations.ts   EMI + eligibility formulas (pure, unit-tested)
    format.ts, structured-data.ts, analytics.ts
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

Phases 1–3 ship the app shell, the public marketing site (home, about,
contact, careers, blog, FAQs, legal pages, loan products, EMI/eligibility
calculators, SEO, analytics), and Phase 2's auth API (not yet wired to any
UI here). Customer/admin/employee/partner portals (Phases 4, 8–11) land as
route groups or sibling apps in this same workspace as their phases come
up.
