# Phase 5 — Lead Management System (LMS)

Status: complete, covering every item `project.md` lists under Phase 5
(Lead Capture, Assignment, Distribution, Scoring, Sources, Duplicate
Detection, Pipeline, Tracking, Analytics, Follow-up Scheduling, Tasks,
Reminders, Auto Assignment, Import Leads, Export Leads) — see "Backfill"
below for the second pass that completed the list after the first pass
covered only Capture/Assignment/Scoring/Pipeline. Builds on Phase 3's
`contact_submissions` and Phase 2's RBAC/audit infrastructure. Zero new
frontend surface — there's no admin/employee portal to show a pipeline in
until Phase 8/9, so this phase is API + backend only, the same shape Phase
2 took relative to Phase 3's login pages.

## Scope

Turn a raw contact-form submission (or a manually-entered/imported
contact) into a real, trackable sales lead: a pipeline status, a
deterministic score, automatic routing to an employee, duplicate
collapsing, follow-up tasks, and aggregate analytics. Explicitly out of
scope: any UI (Phase 9's admin portal owns that), additional lead sources
beyond the contact form and manual entry (LOS applications, Phase 7, will
be a third source later), and anything resembling ML-based scoring (the
AI assistant layer is a separate, later phase — see
`domain/leads/scoring.py`'s docstring for why this stays a simple
rule-based heuristic).

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

## Database schema (migrations `0701461178f7`, `db0c83879dfe`)

`leads`(id, contact_submission_id [FK → contact_submissions, unique,
nullable, CASCADE], source [enum: contact_form/manual], name, email,
phone, status [enum: new/contacted/qualified/converted/disqualified],
score, assigned_to [FK → users, nullable, SET NULL], created_at,
updated_at). `lead_tasks`(id, lead_id [FK → leads, CASCADE], title, notes,
due_at, assigned_to [FK → users, CASCADE], status [enum:
pending/done/cancelled], completed_at, created_at, updated_at). New
permissions `leads.read` / `leads.manage`, granted to
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

## Backfill: completing project.md's full LMS scope

The first pass above covered Lead Capture, Assignment, Scoring, and
Pipeline — 4 of the 15 items `project.md`'s Phase 5 actually lists. Its
own workflow rule ("do not move to the next phase until the current phase
is complete") meant finishing the rest before Phase 6, rather than
carrying the gap forward. This section covers what that backfill added.

**Lead Sources** (`LeadSource`: `CONTACT_FORM` | `MANUAL`) — `Lead` now
carries a `source`, and `contact_submission_id` became nullable: a
manually-created or imported lead never filled out the public contact
form, so pointing it at a fabricated submission row would misrepresent
history. Only two sources are modeled because only two intake mechanisms
exist; LOS applications (Phase 7) become a third real source when that
phase lands, not before.

**Duplicate Detection** — `LeadRepository.find_active_duplicate(email,
phone)` matches on email *or* phone, but only against leads not already
in a terminal status (`TERMINAL_STATUSES`). A resubmission against an
active lead doesn't create a second pipeline entry; it bumps the
existing lead's score by 10 (capped at 100) and audit-logs
`lead.duplicate_submission` — repeated interest is a positive signal, not
noise to discard. A resubmission against a lead that's already
`converted` or `disqualified` *does* create a fresh lead: that's a new
opportunity (a past customer re-engaging), not the same one, and merging
it into closed history would misrepresent the pipeline.

**Auto Assignment / Lead Distribution** — `project.md` lists these as two
items; they're the same mechanism (automatic routing of a new lead to an
owner) and this phase implements it once. `LeadService._auto_assign`
picks the active employee with the fewest currently-open (non-terminal)
leads — least-loaded, not round-robin, because it doesn't need extra
persisted cursor state to stay fair and self-corrects if an employee goes
inactive for a while. Runs automatically after every lead creation
(contact-form submission or import) that isn't a duplicate; falls back to
leaving the lead unassigned if there are no active employees yet, a real
and expected state early on, not an error.

**Lead Analytics** — `GET /leads/analytics/summary`: total count, counts
by status and source, average score, conversion rate. Computed at read
time via `GROUP BY` queries, not maintained incrementally; revisit only
if this becomes a real hot path.

**Lead Tracking** — `GET /leads/{id}/activity` surfaces that lead's slice
of the audit log (`AuditLogRepository.list_for_entity`, new this phase).
No separate "lead history" table: every lead-affecting action already
gets audit-logged (`lead.created`, `lead.duplicate_submission`,
`lead.auto_assigned`, `lead.status_changed`, `lead.assigned`,
`lead.task_created`, `lead.task_completed`), so tracking is a filtered
read over data that already exists, not a second system to keep in sync.

**Follow-up Scheduling, Tasks, and Reminders** — one mechanism
(`LeadTaskEntity`: title, due date, assignee, notes, status), not three.
A reminder *is* a task with a due date; a scheduled follow-up *is* a task
assigned to whoever owns the lead. `POST /{lead_id}/tasks`, `GET
/{lead_id}/tasks`, `GET /tasks/mine` (the assignee's own queue), `POST
/tasks/{id}/complete`. Same assignee validation as lead assignment
(employees/admins only).

**Import / Export Leads** — `POST /leads/import` accepts a JSON array
(not CSV/multipart — the API is JSON-only everywhere else, and there's no
UI yet to justify file upload handling) and runs every item through the
same duplicate-detection + scoring + auto-assignment pipeline a contact
submission gets, so a stale CSV of old contacts doesn't create duplicate
pipeline entries for people already active leads. `GET /leads/export`
streams CSV (the one place JSON would be actively worse — CSV is what
opens in Excel).

### Bugs found in the backfill

**Naming a repository method `list` shadowed the builtin within the class
body, breaking every later method's `list[...]` type hint.** Python
evaluates annotations eagerly at class-definition time (no `from
__future__ import annotations` in this codebase); once `async def
list(...)` executed inside `LeadRepository`/`SqlAlchemyLeadRepository`,
the name `list` in that class body's namespace pointed at the method, not
the builtin. The next method added — `count_open_by_assignee(self,
assignee_ids: list[uuid.UUID])` — failed at import time with `TypeError:
'function' object is not subscriptable`, not something a type checker
catches (it's evaluated, not just annotated). Fixed by renaming to
`list_leads`, which also matches the convention every *other* list method
in this codebase already followed (`list_recent`, `list_active_for_user`,
`list_by_role`, `list_for_lead`, `list_for_assignee`) — the original name
was the actual bug, not just this particular collision.

**Adding an enum column to an existing table needs an explicit `CREATE
TYPE`.** `op.create_table(...)` with an `Enum` column implicitly creates
the Postgres type; `op.add_column(...)` does not. Adding `leads.source`
failed with `UndefinedObjectError: type "lead_source" does not exist`
until the migration explicitly called
`sa.Enum(...).create(op.get_bind(), checkfirst=True)` first. Caught by
inserting a real pre-migration row into a throwaway Postgres container
before trusting the autogenerated migration, then verifying it actually
backfilled correctly (`server_default='contact_form'` on the `ALTER
TABLE ADD COLUMN`, dropped immediately after so it doesn't linger — every
row that existed before this migration really was contact-form-sourced,
since import didn't exist yet).

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
