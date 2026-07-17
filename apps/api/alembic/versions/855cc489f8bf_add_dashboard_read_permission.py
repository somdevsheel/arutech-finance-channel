"""add dashboard read permission

Revision ID: 855cc489f8bf
Revises: 5bf4ba328030
Create Date: 2026-07-17 13:56:33.246260

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '855cc489f8bf'
down_revision: Union[str, Sequence[str], None] = '5bf4ba328030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen at the time this migration was written — not imported from
# `infrastructure.database.seed_data`. See migration c422da52af08's own
# comment (and Phase 5's `0701461178f7`, which found the bug this pattern
# avoids). No new tables this phase — Phase 8's Admin Dashboard is a
# read-only aggregation over data Phases 5-7 already persist — so this
# migration is permission-seeding only.
_NEW_PERMISSIONS: list[tuple[str, str]] = [
    (
        "dashboard.read",
        "View the executive dashboard: KPIs, funnel, heatmap, alerts, system health",
    ),
]
# Admin-only, deliberately not granted to employee — see seed_data.py's
# comment on why this permission is scoped differently from the other
# `*.read` permissions.
_NEW_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": ["dashboard.read"],
}


def upgrade() -> None:
    """Upgrade schema."""
    _seed_dashboard_permission()


def _seed_dashboard_permission() -> None:
    bind = op.get_bind()

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
    )
    roles_table = sa.table("roles", sa.column("id", sa.Uuid()), sa.column("name", sa.String()))
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )

    permission_ids = {code: uuid.uuid4() for code, _ in _NEW_PERMISSIONS}
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[code], "code": code, "description": description}
            for code, description in _NEW_PERMISSIONS
        ],
    )

    role_ids = {
        row.name: row.id
        for row in bind.execute(
            sa.select(roles_table.c.id, roles_table.c.name).where(
                roles_table.c.name.in_(_NEW_ROLE_PERMISSIONS)
            )
        ).fetchall()
    }

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": role_ids[role_name], "permission_id": permission_ids[code]}
            for role_name, codes in _NEW_ROLE_PERMISSIONS.items()
            for code in codes
            if role_name in role_ids
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    permissions_table = sa.table(
        "permissions", sa.column("id", sa.Uuid()), sa.column("code", sa.String())
    )
    codes = [code for code, _ in _NEW_PERMISSIONS]
    op.execute(permissions_table.delete().where(permissions_table.c.code.in_(codes)))
