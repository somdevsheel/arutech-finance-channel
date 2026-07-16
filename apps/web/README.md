# apps/web — Arutech Finance Platform frontend

Next.js 16 (App Router), TypeScript, Tailwind v4, shadcn/ui, TanStack Query,
React Hook Form + Zod, Motion. Built via `create-next-app` and extended for
this project — see [`node_modules/next/dist/docs`](node_modules/next/dist/docs)
for Next.js 16 conventions if something looks unfamiliar (notably: Middleware
is now `proxy.ts`, and `fetch` is uncached by default unless wrapped in
`"use cache"`).

## Structure

```
src/
  app/            Routes (App Router). providers.tsx wires TanStack Query
                   + the toaster around the whole tree.
  components/
    ui/            shadcn/ui primitives (generated, don't hand-edit — re-run
                   `pnpm dlx shadcn@latest add <component>` instead)
    *.tsx          App-specific components (e.g. system-status-card.tsx)
  hooks/          TanStack Query hooks (use-platform-health.ts)
  lib/            api-client.ts (typed fetch wrapper), env.ts (zod-validated
                   env vars), utils.ts (shadcn's cn())
  types/          Shared response/DTO types
  tests/          Vitest setup (jest-dom matchers)
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
— never put a secret there. `API_INTERNAL_URL` is server-only, used by
server components/route handlers to reach the API over the Docker network
(`http://api:8000`); it falls back to `NEXT_PUBLIC_API_URL` when unset, so
local dev without Docker works with just the public URL.

## What's here vs. what's coming

Phase 1 ships the app shell, provider wiring, and a live platform-status
page (`/`) that proves the API connection end-to-end — not the public
marketing site (home/about/pricing/blog — Phase 3) or the customer/admin/
employee/partner portals (Phases 4, 8–11), which land as route groups or
sibling apps in this same workspace as their phases come up.
