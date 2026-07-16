"""Baseline RBAC seed data: a single source of truth shared by the Alembic
migration (`c422da52af08_...`) that seeds a real Postgres/dev database, and
the test suite's `db_session` fixture, which seeds an in-memory SQLite
database the same way — so tests exercise the exact roles/permissions the
app actually ships with, not a parallel hand-maintained copy.
"""

# A small, honest starter permission set tied to what actually exists after
# Phase 2 (auth + RBAC + audit logs) — not speculative loan/CRM permissions
# for features later phases haven't built yet.
PERMISSIONS: list[tuple[str, str]] = [
    ("users.read", "View user profiles"),
    ("users.manage", "Create, update, and deactivate user accounts"),
    ("audit_logs.read", "View the audit log"),
    ("roles.manage", "Manage roles and their permissions"),
]

# Role -> permission codes. Matches the existing `UserRole` enum
# (customer/employee/partner/admin) from Phase 1, which stays the coarse
# actor-type/portal selector; these roles carry the fine-grained
# permissions within that.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [code for code, _ in PERMISSIONS],
    "employee": ["users.read", "audit_logs.read"],
    "partner": [],
    "customer": [],
}
