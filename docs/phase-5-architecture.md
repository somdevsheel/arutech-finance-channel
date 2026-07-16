# Phase 5 — Lead Scoring & Pipeline

Status: complete. Builds on Phase 3's `contact_submissions` (the only lead
source that exists yet) and Phase 2's RBAC/audit infrastructure. Zero new
frontend surface — there's no admin/employee portal to show a pipeline in
until Phase 8/9, so this phase is API + backend only, the same shape Phase
2 took relative to Phase 3's login pages.

## Scope

Turn a raw contact-form submission into a real sales lead: a pipeline
status, a deterministic score, and assignment to an employee. Explicitly
out of scope: any UI (Phase 9's admin portal owns that), additional lead
sources beyond the contact form (LOS applications, Phase 6/7, will be a
second source later), and anything resembling ML-based scoring (the AI
assistant layer is a separate, later phase — see `domain/leads/scoring.py`'s
docstring for why this stays a simple rule-based heuristic).

## Layering

```
domain/leads/        LeadEntity, LeadStatus (+ ALLOWED_TRANSITIONS state
                      machine), LeadRepository interface, scoring.py (a
                      pure, deterministic score_lead() — no DB, no
                      framework).
infrastructure/       models/leads.py (SQLAlchemy Lead model) +
                       repositories/lead_repository.py (the concrete
                       LeadRepository, following user_repository.py's
                       precedent of raising NotFoundError itself on
                       update_status/assign rather than returning None).
services/lead_service.py   create_from_contact_submission, get_lead,
                            list_leads, update_status (validates the
                            transition), assign (validates the assignee
                            is an employee/admin). Audit-logs every
                            create/status-change/assignment, matching
                            Phase 2's discipline.
services/contact_service.py   Now takes a LeadService dependency and
                                calls create_from_contact_submission right
                                after persisting the submission — the
                                same constructor-injection pattern
                                AuthService uses for AuditService, not
                                orchestration in the endpoint.
api/v1/schemas/leads.py        LeadResponse, LeadStatusUpdateRequest,
                                 LeadAssignRequest.
api/v1/endpoints/leads.py       GET /leads, GET /leads/{id}, POST
                                  /leads/{id}/status, POST
                                  /leads/{id}/assign. Explicit
                                  action-named endpoints (matching
                                  /auth/logout-all, /auth/password-reset/
                                  confirm) instead of a generic PATCH, so
                                  each mutation can carry its own
                                  validation and audit action name.
```

There is deliberately no public `POST /leads`: leads only ever originate
from the contact-form pipeline right now (or, later, other real intake
surfaces) — never from a direct API call, same reasoning as Phase 2's "no
public path to self-register into a privileged role."

## Key design decisions

**Lead is a thin, self-contained record referencing its `ContactSubmission`
by ID, not joined to it at read time.** `name`/`email`/`phone` are copied
onto the lead at creation. This isn't denormalization for its own sake: an
employee correcting a typo'd phone number on a lead shouldn't mean editing
the original submission (which is an immutable, append-only audit record —
see Phase 3's `ContactSubmission` model comment), and every list/detail
read would otherwise need a join for data that rarely diverges.

**The pipeline is a real state machine, not a free-text status field.**
`ALLOWED_TRANSITIONS` in `domain/leads/entities.py` is the single source of
truth for what transitions are legal: NEW → CONTACTED/DISQUALIFIED →
QUALIFIED/DISQUALIFIED → CONVERTED/DISQUALIFIED, with CONVERTED and
DISQUALIFIED terminal. `LeadService.update_status` checks this before
touching the database and raises `ConflictError` (409) otherwise — you
cannot skip a stage, go backward, or reopen a closed lead by hitting the
API directly. A test exists for every legal and several illegal
transitions (`test_lead_transitions.py`).

**Scoring is one small, inspectable, testable function — explicitly not a
model.** `score_lead()` adds points for a phone number (reachability), a
substantive message (signals real intent over a one-liner), and
loan-related language in the subject/message (keyword match against a
short, honest list). It's a starting point for triage ordering (leads list
sorted by score), not a claim about conversion probability. Revisiting
this with real outcome data (once there are enough conversions to learn
from) is future work, not this phase's.

**Leads can only be assigned to employees or admins**, enforced in the
service layer (`ConflictError` if the target user's role is
customer/partner), not just by convention — an assignment endpoint that
silently accepted any user ID would be a real bug the first time someone
fat-fingered a customer's ID.

## Database schema (migration `0701461178f7`)

`leads`(id, contact_submission_id [FK → contact_submissions, unique, CASCADE],
name, email, phone, status [enum: new/contacted/qualified/converted/
disqualified], score, assigned_to [FK → users, nullable, SET NULL], created_at,
updated_at). New permissions `leads.read` / `leads.manage`, granted to
admin and employee (customer/partner get neither, matching Phase 2's
existing pattern for `users.*`/`audit_logs.*`).

## Bugs found building this phase

**Phase 2's own RBAC-seeding migration (`c422da52af08`) imported the
*live* `seed_data.PERMISSIONS`/`ROLE_PERMISSIONS` instead of freezing its
own historical snapshot.** That module's lists are meant to keep growing
(this phase added two entries to them), and a migration importing the
live module means `alembic upgrade head` on a fresh database re-seeds
whatever `seed_data.py` looks like *today* — not what Phase 2 actually
shipped. The instant this phase added `leads.read`/`leads.manage` to
`seed_data.py`, a fresh install started inserting those permissions
*twice*: once from `c422da52af08` (now unintentionally seeding six
permissions instead of its original four) and once from this phase's own
migration, tripping a unique-constraint violation on `permissions.code`
and failing `alembic upgrade head` from scratch. Caught by running the
CI migration check (`upgrade head` → `downgrade base` → `upgrade head`)
against a throwaway Postgres container before trusting the new migration.
Fixed by freezing `c422da52af08`'s own copy of the original four
permissions inline in the migration file — a migration is a historical
record and must not depend on app code that changes after it's written.
This phase's own migration (`0701461178f7`) was written the correct way
from the start: `_NEW_PERMISSIONS`/`_NEW_ROLE_PERMISSIONS` are local,
frozen constants, not an import from `seed_data`.

## Security

Both new endpoints families require authentication; `leads.read` gates
listing/viewing, `leads.manage` gates status changes and assignment —
re-checked from the database on every request via the same
`require_permission` dependency Phase 2 built (not cached in the access
token). Every lead creation, status change, and assignment is
audit-logged with actor, action, and metadata (previous/new status,
assignee), so "who moved this lead to disqualified and when" is always
answerable — the same audit bar Phase 2 set for auth-relevant actions,
now extended to the first CRM-shaped one.
