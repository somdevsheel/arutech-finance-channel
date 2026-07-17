# Phase 7 — Loan Origination System (LOS)

Status: complete, covering every item `project.md` lists under Phase 7
(Application, KYC, Eligibility, Verification, Document Collection, Credit
Assessment, Bank Routing, Approval, Sanction Letter, Disbursement,
Commission Tracking, Loan Closure) with a few explicitly-scoped
simplifications — see "Honest simplifications" below. Builds on Phase 1's
`User`, Phase 5's `Lead` (provenance only), Phase 2's RBAC/audit
infrastructure, and Phase 3's `loan-products.ts` catalog (mirrored, not
shared — see `domain/loans/products.py`). This is the phase that unblocks
what Phase 4 (Customer Portal) and Phase 6 (CRM) both deferred: "Loan
Status" and "Loan History" finally have something real to show.

## Scope

The full application lifecycle: a customer applies, submits, gets
reviewed (KYC + income/employment verification + an automated
eligibility check + a heuristic credit assessment), gets approved or
rejected, gets sanctioned with specific terms, gets disbursed, and
eventually closes — with a document checklist and commission tracking
running alongside. Unlike Phase 5/6, this phase is **not** backend-only:
it also updates Phase 4's customer portal (see "Frontend integration"
below), because Phase 4 explicitly deferred "Loan Status" to exactly this
point.

## Layering

```
domain/loans/
  entities.py          LoanApplicationEntity (customer_user_id, product,
                        amount/tenure/rate, income, and every pipeline
                        field below), LoanApplicationStatus + its
                        ALLOWED_TRANSITIONS state machine, KycStatus,
                        VerificationStatus, EligibilityStatus,
                        RiskCategory, CommissionStatus, LoanDocumentEntity
                        + LoanDocumentStatus, LoanAnalyticsSummary.
  calculations.py       calculate_emi / assess_eligibility ported
                         line-for-line from
                         apps/web/src/lib/loan-calculations.ts (see
                         below); assess_credit, a separate honest
                         heuristic with no frontend equivalent.
  products.py            LOAN_PRODUCTS — slug, rate/tenure/amount bounds,
                          and required-documents list, mirrored from
                          apps/web/src/content/loan-products.ts.
  repository.py / document_repository.py   LoanApplicationRepository +
                                             LoanDocumentRepository —
                                             split the same way Phase
                                             5 split Lead/LeadTask.
services/
  loan_application_service.py   Every pipeline transition, each
                                  validated and audit-logged; owns
                                  commission calculation.
  loan_document_service.py       Checklist listing, customer
                                  self-submission, staff review.
api/v1/schemas/loans.py, api/v1/endpoints/loans.py   /api/v1/loan-
  applications — a dual-access resource (see "Access control" below),
  the first phase where that pattern was needed.
```

## Key design decisions

**EMI and eligibility math is ported line-for-line from the frontend,
not reimplemented from scratch.** `apps/web/src/lib/loan-calculations.ts`
already has a tested reducing-balance EMI formula and a FOIR-based
eligibility calculator (Phase 3's pre-qualification tool). Two
independent implementations of the same formula drifting apart over time
would be worse than either being simplified — see `calculate_emi`'s and
`assess_eligibility`'s docstrings for the exact correspondence. The
frontend calculator *inverts* the formula (income → max loan, for
pre-qualification before applying); the backend runs it *forward*
(specific requested EMI → fits within FOIR or not, for an application
that already has a concrete amount).

**Credit assessment is a small, deterministic, documented heuristic —
explicitly not a real bureau check.** No CIBIL/Experian integration
exists. `assess_credit` buckets the EMI-to-income ratio into a 0-100
score and LOW/MEDIUM/HIGH risk, the same honesty `domain/leads/
scoring.py` established for lead scoring in Phase 5: real bureau
integration is a distinct, later, explicitly-scoped feature, not
something to fake with an invented "score."

**Sub-statuses, not more top-level pipeline states.** KYC, verification,
eligibility, and credit assessment all happen *during* `UNDER_REVIEW`, in
parallel, not as a fixed sequence — so they're separate fields on the
entity, not additional states in `ALLOWED_TRANSITIONS`. `APPROVED` is
only reachable once `kyc_status == VERIFIED`, `verification_status ==
VERIFIED`, and `eligibility_status == ELIGIBLE` all hold — a real,
enforced gate (`LoanApplicationService.approve`), not just a label.

**`LoanApplicationRepository.update` takes a whole entity, breaking the
narrow-setter pattern Lead/CustomerProfile established.** Sanctioning
alone sets three fields at once (amount, tenure, date); disbursement sets
five. Per-field setters for a 24-field entity with this many
multi-field transitions would be more surface area, not less — the
docstring on `update()` explains why this is the one deliberate
exception, and that the service layer is the only caller, always via
`dataclasses.replace()` on an entity it just read (never a blind partial
overwrite).

**Access control needed a new pattern: ownership, not just permission.**
Every prior phase (5, 6) was staff-only. A loan application has two
legitimate audiences — the applicant and staff reviewing it — so the
router has two route families under the same prefix: `/mine/*` (any
authenticated `customer`-role user, ownership checked in the service
layer) and everything else (`loans.read`/`loans.manage`, same
`require_permission` pattern as before). `get_own` returns 404, never
403, for someone else's application — a 403 would confirm to a caller
that some other application ID is valid, just not theirs; see its
docstring.

## Honest simplifications

**Document Collection tracks a checklist, not files.** `LoanDocument` has
a `document_type` (free text — required documents vary too widely across
7 products for a fixed enum to fit all of them) and a status
(pending/submitted/verified/rejected), auto-seeded from the product's
`documents_required` on submission. There's no file upload, storage, or
retrieval — that's Phase 12's Document Management System (OCR, encryption,
versioning, virus scanning). Building file storage now would preempt a
phase that explicitly owns it.

**Bank Routing is internal employee assignment, not multi-lender
routing.** Real routing — choosing among partner banks/NBFCs — needs
Bank/NBFC entities that don't exist until Phase 9 ("Bank Management",
"NBFC Management") and a Partner Bank Portal (Phase 11) to receive them.
What Phase 7 builds instead is `assigned_to` (an employee/admin who owns
the application), the same mechanism Phase 5 used for lead assignment.

**Sanction Letter is structured data, not a generated PDF.** Sanctioning
captures `sanctioned_amount`, `sanctioned_tenure_months`, and
`sanction_date` as real fields — a genuine business event — without
rendering a downloadable document. PDF generation/templating is a
Document Management concern (Phase 12), not invented here.

**Commission Tracking uses one flat rate (1% of disbursed amount), not
per-partner rate configuration.** `COMMISSION_RATE_PERCENT` in
`loan_application_service.py` is a constant. Real rate management —
different rates per bank/NBFC/partner — is Phase 9's "Commission
Management" / Phase 11's Partner Bank Portal territory. This phase makes
sure a commission number exists and is tracked (PENDING → APPROVED →
PAID) at all, rather than building a rate-configuration system ahead of
the phases that would actually drive it.

## Frontend integration

Unlike Phase 5/6, this phase touches `apps/web`: Phase 4's customer
portal dashboard had an explicit placeholder — "You don't have any
applications yet... coming in a later phase." This phase replaces it with
a real flow, all under the existing customer-portal BFF (Server Actions,
httpOnly session cookies) Phase 4 established — no new auth pattern, just
new Server Actions and Server Component reads following it:

```
lib/loans/
  session.ts        Read-only Server Component fetches (getOwnLoanApplications,
                     getOwnLoanApplication, getOwnLoanDocuments) — mirrors
                     lib/auth/session.ts exactly, including why it's read-only
                     (proxy.ts already guarantees a fresh access token).
  actions.ts         applyForLoanAction (create + submit collapsed into one
                     action — see its docstring), withdrawApplicationAction,
                     submitDocumentAction.
  schemas.ts          Loose zod bounds (just "positive") — the real per-
                       product min/max lives only in the backend's
                       products.py and is enforced there; duplicating it a
                       third time (frontend content + backend catalog is
                       already the accepted duplication) wasn't worth it.
app/(portal)/applications/          List, apply, and [id] detail pages —
                                     see "Bugs found" for why this isn't
                                     named app/(portal)/loans/.
components/portal/    LoanApplicationCard, LoanStatusBadge, LoanApplyForm,
                       DocumentChecklist, WithdrawApplicationButton.
```

The marketing loan product detail page (`(marketing)/loans/[slug]`) got
an "Apply Now" button linking to `/applications/apply?product={slug}`;
`proxy.ts`'s login redirect was extended to preserve the full path +
query string (previously pathname-only), so a logged-out visitor clicking
"Apply Now" for a specific product still lands on that same pre-filled
form after signing in instead of a generic blank one.

### Bugs found integrating the frontend

**`app/(portal)/loans/` collided with the already-existing
`app/(marketing)/loans/`.** Route groups (the parenthesized
`(portal)`/`(marketing)` folders) are purely organizational — they don't
add a URL segment — so `(portal)/loans/[id]/page.tsx` and
`(marketing)/loans/[slug]/page.tsx` both resolved to the identical
`/loans/[*]` URL pattern, and `(portal)/loans/page.tsx` collided with the
marketing product listing at `/loans` the same way. Next.js's own build
step catches this ("Ambiguous app routes detected") — `next build`, not
`tsc` or `eslint`, which both passed cleanly beforehand. Fixed by renaming
the customer-facing route to `/applications`, which also reads more
clearly for "the loans *I've* applied for" versus `/loans`, the public
product catalog. Caught by actually running a production build before
calling the frontend work done, not just typecheck/lint/tests — the same
"verify by running it" discipline this project applies to migrations.

## Database schema (migration `5bf4ba328030`)

`loan_applications`(id, customer_user_id [FK → users, CASCADE], lead_id
[FK → leads, nullable, SET NULL], loan_product_slug, requested_amount,
tenure_months, interest_rate [numeric(5,2)], monthly_income,
existing_monthly_obligations, status [enum], kyc_status [enum],
verification_status [enum], eligibility_status [enum], credit_score,
risk_category [enum, nullable], assigned_to [FK → users, nullable, SET
NULL], rejection_reason, sanctioned_amount, sanctioned_tenure_months,
sanction_date, disbursed_amount, disbursement_date,
disbursement_reference, commission_amount, commission_status [enum,
nullable], closure_date, closure_reason, created_at, updated_at).
`loan_documents`(id, application_id [FK → loan_applications, CASCADE],
document_type, status [enum], notes, created_at, updated_at). New
permissions `loans.read` / `loans.manage`, granted to admin and employee
— following the frozen-migration-constant pattern `0701461178f7` (Phase
5) established after finding the live-import bug in `c422da52af08`.

## Security

Staff routes: `loans.read`/`loans.manage`, re-checked from the database
per request, same as every prior phase. Customer routes: authenticated +
`role == customer` + ownership, checked in the service layer, not a
`require_permission` dependency — there's no "own this specific record"
permission code, and there shouldn't be one; ownership is a property of
the data, not a role grant. Every pipeline transition (create, submit,
withdraw, assign, KYC/verification updates, approve, reject, sanction,
disburse, commission update, close, document submit/review) is
audit-logged with actor and metadata, extending the same "who did what
and when" guarantee Phase 2 set and Phase 5/6 carried forward.
