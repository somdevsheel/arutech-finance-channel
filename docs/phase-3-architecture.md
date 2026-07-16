# Phase 3 — Public Website

Status: complete. Mostly `apps/web`; one backend addition (contact
submissions). Builds on Phase 1's app shell and Phase 2's nothing directly
(this phase has no auth-gated pages) — the public site is intentionally
usable without an account.

## Scope

Home, About, Contact, Careers, Blog, FAQs, Privacy Policy, Terms,
Disclaimer, Loan Products, EMI Calculator, Eligibility Calculator, SEO,
Analytics. Out of scope: a CMS (Phase 9 owns that), real notification
delivery for contact submissions (Phase 13), and lead scoring/pipeline for
those submissions (Phase 5).

## Structure

```
apps/web/src/
  app/
    (marketing)/          Route group: header/footer layout wraps every
                            public page. Maps to / (not /marketing/...).
      page.tsx              Home
      about/, careers/, contact/, faqs/, privacy-policy/, terms/,
      disclaimer/           Static/mostly-static pages
      blog/, blog/[slug]/    Index + detail, generateStaticParams
      loans/, loans/[slug]/  Index + detail, generateStaticParams
      tools/emi-calculator/, tools/eligibility-calculator/
      opengraph-image.tsx    Shared OG image (next/og ImageResponse)
    status/                 Relocated from / — see below
    sitemap.ts, robots.ts    Next.js file-convention SEO endpoints
  content/                 Static typed content: loan-products.ts,
                             blog-posts.ts, faqs.ts, job-openings.ts,
                             nav-links.ts
  lib/
    loan-calculations.ts    EMI + eligibility formulas (pure, unit-tested)
    format.ts               INR currency + date formatting
    structured-data.ts      JSON-LD builders (Organization, FAQPage, Article)
    analytics.ts            GA4 wrapper, no-op without a measurement ID
  components/
    site-header.tsx, site-footer.tsx
    marketing/              Section building blocks, calculator forms,
                             contact form, legal-page renderer
    analytics/google-analytics.tsx
```

Backend: `domain/contact/`, `infrastructure/database/models/contact.py` +
repository, `services/contact_service.py`, `api/v1/endpoints/public.py`
(`POST /api/v1/public/contact`) — same layered pattern as every prior
phase.

## Key decisions

**Content is static typed data, not a CMS.** Phase 9 explicitly owns "CMS"
as an admin-editable feature. Blog posts, loan products, FAQs, and job
listings live in `src/content/*.ts`. The shapes (slug, title, structured
sections) are deliberately close to what a future CMS-backed API response
would look like, so swapping the data source later touches the content
layer, not the page components.

**`/` moved from Phase 1's system-status page to the real homepage; status
moved to `/status`.** Showing internal service names/versions on a public
marketing site is an information-disclosure smell, not a feature.
`/status` is `noindex` and disallowed in `robots.ts`. It has no auth gate
yet (no admin portal exists to gate it behind) — that's a known gap to
close whenever Phase 8/9's admin shell lands.

**Contact form submissions are real, not decorative.** They hit `POST
/api/v1/public/contact`, validated and stored via the same
domain/service/repository layering as every other feature. Deliberately
thin: it does not do lead scoring, assignment, or routing — that's Phase 5
("Lead Capture"). A hidden honeypot field (`website`, CSS-hidden rather
than `type="hidden"`, since some bots specifically skip literal hidden
inputs) silently no-ops spam submissions rather than rejecting them
outright, so scrapers don't learn to leave the field blank.

**EMI and Eligibility Calculators are pure client-side math, tested as
pure functions.** `calculateEmi` and `calculateEligibility` in
`lib/loan-calculations.ts` have no I/O — no server round-trip needed, and
correctness is verified with unit tests reproducing known reference EMI
values, not just "the form renders." The eligibility formula assumes a
50% FOIR (Fixed Obligation to Income Ratio) ceiling by default, disclosed
in the UI copy, and both tools are explicitly labeled as estimates, not
credit decisions — reinforced by the Disclaimer page.

**Legal pages (Privacy/Terms/Disclaimer) are complete, realistic drafts**,
flagged with a source-level comment for legal review before real
production use — appropriate given this is a lending-adjacent, regulated
domain and I'm not a lawyer. No fabricated performance metrics anywhere on
the site (no "50,000+ customers" or "₹500 Cr disbursed" claims) — this is
a platform with no real operating history yet, so marketing copy sticks to
capabilities and process, not invented usage numbers.

**Analytics is GA4 via `next/script`, entirely gated on
`NEXT_PUBLIC_GA_MEASUREMENT_ID`.** Unset in every dev/CI environment (the
default), so `<GoogleAnalytics />` renders nothing and `trackEvent`/
`trackPageview` are no-ops — verified by a unit test that asserts `gtag`
is never called under the test environment's actual (unset) config, not
just that the function doesn't throw.

## SEO

Per-page `metadata` (static or `generateMetadata` for dynamic routes) on
every one of the 15 public route templates · `sitemap.ts` (all static
routes + every loan product + every blog post) · `robots.ts` (disallows
`/status`) · JSON-LD: `Organization` on the homepage, `FAQPage` on `/faqs`,
`Article` on each blog post · a shared dynamic OG image via `next/og`.

## Bugs found building this phase

**shadcn's `Button` here is Base UI-flavored, not Radix — `asChild`
doesn't exist on it.** Base UI uses a `render` prop instead
(`<Button render={<Link href="/x" />}>Text</Button>`, not `<Button asChild>
<Link>Text</Link></Button>`). This wasn't caught in Phase 1 because the
only interactive component built there was a status card with no
polymorphic buttons. Every `<Button asChild>` usage across the new pages
had to be rewritten to the `render` pattern — a real, repository-wide
typecheck failure, not a cosmetic one.

**`z.coerce.number()` fields need explicit `useForm` generics.** Zod's
coercion schemas have a different input type (effectively `unknown`, since
they accept anything and coerce it) from their output type (`number`).
`useForm<T>()` with a single generic assumes input and output are the
same shape, which fails to typecheck against `zodResolver` for any schema
using `z.coerce`. Fixed by passing `useForm<z.input<Schema>, unknown,
z.output<Schema>>()` — the officially recommended pattern, applied to both
calculator forms.

**shadcn's `form` registry component was an empty stub in this shadcn
version** (`{"name": "form", "type": "registry:ui"}`, no files). Built the
EMI/eligibility/contact forms directly with `react-hook-form` +
Label/Input/Textarea instead of shadcn's `FormField` sugar — functionally
equivalent, just without the wrapper's shared error-message boilerplate.
