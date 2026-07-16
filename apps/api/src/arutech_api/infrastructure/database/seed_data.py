"""Baseline RBAC seed data: a single source of truth shared by the Alembic
migration (`c422da52af08_...`) that seeds a real Postgres/dev database, and
the test suite's `db_session` fixture, which seeds an in-memory SQLite
database the same way — so tests exercise the exact roles/permissions the
app actually ships with, not a parallel hand-maintained copy.
"""

# A small, honest starter permission set tied to what actually exists —
# not speculative permissions for features later phases haven't built yet.
# `leads.*` (Phase 5) is the first genuinely CRM-shaped permission pair;
# see migration 8f1c2a9b6d4e for how it was added without re-seeding the
# permissions Phase 2 already inserted.
PERMISSIONS: list[tuple[str, str]] = [
    ("users.read", "View user profiles"),
    ("users.manage", "Create, update, and deactivate user accounts"),
    ("audit_logs.read", "View the audit log"),
    ("roles.manage", "Manage roles and their permissions"),
    ("leads.read", "View leads"),
    ("leads.manage", "Update lead status and assignment"),
]

# Role -> permission codes. Matches the existing `UserRole` enum
# (customer/employee/partner/admin) from Phase 1, which stays the coarse
# actor-type/portal selector; these roles carry the fine-grained
# permissions within that.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [code for code, _ in PERMISSIONS],
    "employee": ["users.read", "audit_logs.read", "leads.read", "leads.manage"],
    "partner": [],
    "customer": [],
}
