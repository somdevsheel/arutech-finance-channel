# Phase 6 — Customer Relationship Management (CRM)

Status: complete, covering every item `project.md` lists under Phase 6
except two explicitly deferred for a real dependency gap (see "Deferred,
not skipped" below). Builds on Phase 1's `User`/`UserRole` and Phase 2's
RBAC/audit infrastructure. Zero new frontend surface, same reasoning as
Phase 5: there's no admin/employee portal to show a CRM in until Phase
8/9, so this is API + backend only.

## Scope

Manage the platform's relationship with every `customer`-role `User`:
a profile (relationship manager, segment, tags), a log of touchpoints
(calls, emails, WhatsApp, meetings, notes), a merged chronological
timeline, and aggregate analytics. Explicitly out of scope: any UI, and
two `project.md` items that don't have real data to operate on yet (see
below).

## Layering

```
domain/crm/           CustomerProfileEntity, CustomerSegment,
                       InteractionEntity, InteractionChannel,
                       InteractionDirection, CustomerAnalyticsSummary,
                       CustomerRepository + InteractionRepository
                       interfaces (split the same way Phase 5 split
                       LeadRepository/LeadTaskRepository — two aggregate
                       roots, two repositories).
infrastructure/        models/crm.py (CustomerProfile, Tag, the
                        customer_tags join table, Interaction) +
                        repositories/customer_repository.py +
                        repositories/interaction_repository.py.
services/customer_service.py    Profile lookup (lazy get-or-create),
                                  listing/filtering, relationship-manager
                                  assignment, segmentation, tags,
                                  analytics, and the timeline merge.
services/interaction_service.py  Logging and listing interactions —
                                   separate from CustomerService the same
                                   way LeadTaskService is separate from
                                   LeadService.
api/v1/schemas/crm.py            Request/response DTOs.
api/v1/endpoints/customers.py    GET/POST under /api/v1/customers,
                                   requiring customers.read or
                                   customers.manage.
```

## Key design decisions

**`CustomerProfile` doesn't duplicate `name`/`email` the way `LeadEntity`
copies contact-submission fields (Phase 5).** A profile always extends a
permanent, already-authoritative `User` record — joining for display data
can't drift the way Lead's snapshot could, and Lead's whole reason for
denormalizing was decoupling from a submission that intentionally
*shouldn't* keep changing underneath it. Here that reasoning doesn't
apply, so the API layer joins `UserRepository` when building a response
instead.

**A profile is created lazily, on first CRM touch, not at registration.**
`CustomerService` never calls anything from Phase 2 — coupling Phase 6
into the registration flow would mean either reaching backward into an
earlier phase's code or duplicating profile-creation logic in two places.
`get_or_create_profile` is idempotent and cheap, so the first `GET
/customers/{id}`, tag, segment change, RM assignment, or interaction for
a given customer just materializes the row transparently.

**Call Logs, Email Logs, WhatsApp Logs, Meeting History, and Follow-up
Notes are one `Interaction` table with a `channel` discriminator, not
five.** Same consolidation Phase 5 applied to follow-up scheduling/tasks/
reminders — these are the same underlying concept (a logged touchpoint)
differing only in medium, and a channel enum captures that difference
without five near-identical tables.

**Segmentation is a small, honest, manually-assigned enum
(`new`/`active`/`high_value`/`at_risk`/`dormant`), not computed.** Real
automated segmentation needs loan value and engagement data that doesn't
exist until Phase 7 (LOS) — inventing a scoring formula off data that
isn't real would be worse than an honest manual field, the same
reasoning `domain/leads/scoring.py` documented for why lead scoring stays
a simple heuristic rather than pretending to be ML.

**Tags are a shared, reusable pool (a real many-to-many), not free text
per customer.** `GET /customers/tags` lists every tag in use — consistent
naming and a real autocomplete source beat "VIP" vs "vip" vs "Vip"
fragmenting silently across profiles.

**Customer Timeline is a merge of two existing data sources, not a third
system to keep in sync.** `CustomerService.get_timeline` reads
`AuditLogRepository.list_for_entity("customer", user_id)` (relationship-
manager changes, segment changes, tag changes — everything already
audit-logged) and `InteractionRepository.list_for_customer`, then sorts
the union chronologically. Every action that should appear on a timeline
was already being recorded somewhere; this phase didn't need a new
"history" table, just a read that reaches into both.

**Assignability is validated by role, matching Lead assignment's
pattern exactly:** a relationship manager must be `employee` or `admin`
(409 otherwise), and CRM operations reject non-`customer`-role users with
409 (not 404 — the user exists, it's just the wrong kind of user for this
endpoint) while a genuinely unknown user ID is 404.

## Deferred, not skipped

**Document History and Loan History** are the two `project.md` Phase 6
items not built here. Neither has real data to show yet: there's no
Document Management System until Phase 12, and no Loan Origination
System until Phase 7 — a "Loan History" endpoint today could only ever
return an empty list, which isn't a feature, it's a placeholder pretending
to be one. Phase 4's Customer Portal deferred "Loan Status"/"Documents"
for the identical reason; Customer 360 will grow these sections when
Phase 7/12 give them something real to display, not before.

## Database schema (migration `c7c3ce2e47cc`)

`customer_profiles`(id, user_id [FK → users, unique, CASCADE],
relationship_manager_id [FK → users, nullable, SET NULL], segment [enum],
created_at, updated_at). `tags`(id, name [unique]). `customer_tags`
(customer_profile_id, tag_id — join table). `interactions`(id,
customer_user_id [FK → users, CASCADE], channel [enum], direction [enum],
summary, notes, occurred_at, logged_by [FK → users, CASCADE],
created_at — append-only, no `updated_at`, same reasoning as Phase 3's
`contact_submissions`). New permissions `customers.read` /
`customers.manage`, granted to admin and employee — following
`0701461178f7`'s pattern (Phase 5) of freezing the migration's own
permission delta rather than importing the live, ever-growing
`seed_data.py`, which is exactly the bug that phase found and fixed in
`c422da52af08`.

## Security

Same model as Phase 5's leads: `customers.read` gates every GET,
`customers.manage` gates every mutation, both re-checked from the
database on every request via `require_permission` (never cached in the
access token). Every relationship-manager change, segment change, tag
add/remove, and interaction log is audit-logged with actor and metadata —
the CRM gets the same "who did what and when" guarantee Phase 2 set for
auth and Phase 5 extended to leads.
