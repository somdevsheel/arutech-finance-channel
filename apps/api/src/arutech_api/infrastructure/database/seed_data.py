"""Baseline RBAC seed data: a single source of truth shared by the Alembic
migration (`c422da52af08_...`) that seeds a real Postgres/dev database, and
the test suite's `db_session` fixture, which seeds an in-memory SQLite
database the same way — so tests exercise the exact roles/permissions the
app actually ships with, not a parallel hand-maintained copy.
"""

# A small, honest starter permission set tied to what actually exists —
# not speculative permissions for features later phases haven't built yet.
# `leads.*` (Phase 5, migration 0701461178f7) and `customers.*` (Phase 6,
# migration — see that migration's own module for the added-in-this-
# migration constants; this list is the current full picture, not a
# historical record — see c422da52af08's own comment for why migrations
# never import this module directly).
PERMISSIONS: list[tuple[str, str]] = [
    ("users.read", "View user profiles"),
    ("users.manage", "Create, update, and deactivate user accounts"),
    ("audit_logs.read", "View the audit log"),
    ("roles.manage", "Manage roles and their permissions"),
    ("leads.read", "View leads"),
    ("leads.manage", "Update lead status and assignment"),
    ("customers.read", "View customer profiles, interactions, and analytics"),
    ("customers.manage", "Update customer segment, tags, relationship manager, and interactions"),
    ("loans.read", "View loan applications, documents, and analytics"),
    ("loans.manage", "Review, approve, sanction, disburse, and close loan applications"),
]

# Role -> permission codes. Matches the existing `UserRole` enum
# (customer/employee/partner/admin) from Phase 1, which stays the coarse
# actor-type/portal selector; these roles carry the fine-grained
# permissions within that.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [code for code, _ in PERMISSIONS],
    "employee": [
        "users.read",
        "audit_logs.read",
        "leads.read",
        "leads.manage",
        "customers.read",
        "customers.manage",
        "loans.read",
        "loans.manage",
    ],
    "partner": [],
    "customer": [],
}
