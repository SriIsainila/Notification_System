"""Ensure tracked item scheduling and lifecycle fields exist.

Revision ID: 20260727_05
Revises: 20260723_04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260727_05"
down_revision: str | None = "20260723_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("tracked_items")}

    if "status" not in columns:
        op.add_column(
            "tracked_items",
            sa.Column("status", sa.String(16), server_default="active", nullable=False),
        )
    if "check_frequency" not in columns:
        op.add_column(
            "tracked_items",
            sa.Column("check_frequency", sa.Integer(), server_default="5", nullable=False),
        )
    if "last_checked_at" not in columns:
        op.add_column(
            "tracked_items",
            sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        )

    inspector = sa.inspect(bind)
    for constraint in inspector.get_check_constraints("tracked_items"):
        name = constraint.get("name")
        sqltext = (constraint.get("sqltext") or "").lower()
        if name and "status" in sqltext:
            op.drop_constraint(name, "tracked_items", type_="check")

    op.create_check_constraint(
        "ck_tracked_items_status",
        "tracked_items",
        "status IN ('active', 'paused', 'removed')",
    )


def downgrade() -> None:
    op.execute("UPDATE tracked_items SET status = 'paused' WHERE status = 'removed'")
    op.drop_constraint("ck_tracked_items_status", "tracked_items", type_="check")
    op.create_check_constraint(
        "ck_tracked_items_status",
        "tracked_items",
        "status IN ('active', 'paused')",
    )
