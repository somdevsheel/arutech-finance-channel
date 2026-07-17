"""Baseline RBAC seed data: a single source of truth shared by the Alembic
migration (`c422da52af08_...`) that seeds a real Postgres/dev database, and
the test suite's `db_session` fixture, which seeds an in-memory SQLite
database the same way — so tests exercise the exact roles/permissions the
app actually ships with, not a parallel hand-maintained copy.
"""

# A small, honest starter permission set tied to what actually exists —
# not speculative permissions for features later phases haven't built yet.
# `leads.*` (Phase 5, migration 0701461178f7), `customers.*` (Phase 6),
# `loans.*` (Phase 7, migration 5bf4ba328030), and `dashboard.read` (Phase
# 8) were each added by their own migration — see that migration's own
# module for the added-in-this-migration constants; this list is the
# current full picture, not a historical record — see c422da52af08's own
# comment for why migrations never import this module directly.
# `dashboard.read` is deliberately admin-only (not granted to `employee`
# below) — the executive dashboard is exec-level aggregate data across the
# whole business, a different audience than the per-record `*.read`
# permissions employees already have. Every Phase 9 permission
# (lenders/loan_products/notification_templates/cms/settings) is
# admin-only for the same reason: project.md frames all of Phase 9 as
# "Admin Panel" — back-office catalog/config management, not the
# day-to-day operational work `leads.*`/`customers.*`/`loans.*` cover.
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
    (
        "dashboard.read",
        "View the executive dashboard: KPIs, funnel, heatmap, alerts, system health",
    ),
    ("lenders.read", "View the bank/NBFC lender catalog"),
    ("lenders.manage", "Create, update, and (de)activate lenders"),
    ("loan_products.read", "View the loan product catalog"),
    ("loan_products.manage", "Create, update, and (de)activate loan products"),
    ("notification_templates.read", "View notification templates"),
    ("notification_templates.manage", "Create, update, and (de)activate notification templates"),
    ("cms.read", "View CMS content, including unpublished drafts"),
    ("cms.manage", "Create, update, publish, and unpublish CMS content"),
    ("settings.read", "View system settings"),
    ("settings.manage", "Update system settings"),
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
