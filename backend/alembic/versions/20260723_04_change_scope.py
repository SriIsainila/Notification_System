"""Add tracked change notification scope.

Revision ID: 20260723_04
Revises: 20260722_03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260723_04"
down_revision = "20260722_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tracked_items",
        sa.Column("change_scope", sa.String(length=16), nullable=False, server_default="all"),
    )
    op.create_check_constraint(
        "ck_tracked_items_change_scope",
        "tracked_items",
        "change_scope IN ('price', 'stock', 'all')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tracked_items_change_scope", "tracked_items", type_="check")
    op.drop_column("tracked_items", "change_scope")
