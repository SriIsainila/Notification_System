"""Create or upgrade tracked_items for URL tracking.

Revision ID: 20260722_02
Revises: 20260722_01
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260722_02"
down_revision: str | None = "20260722_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "tracked_items" not in inspector.get_table_names():
        op.create_table(
            "tracked_items",
            sa.Column("item_id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("normalized_url", sa.Text(), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("image_url", sa.Text()),
            sa.Column("store_name", sa.String(120)),
            sa.Column("status", sa.String(16), server_default="active", nullable=False),
            sa.Column("check_frequency", sa.Integer(), server_default="60", nullable=False),
            sa.Column("target_price", sa.Numeric(12, 2)),
            sa.Column("notify_channel", sa.String(16), server_default="email", nullable=False),
            sa.Column("current_price", sa.Numeric(12, 2)),
            sa.Column("currency", sa.String(10), server_default="LKR", nullable=False),
            sa.Column("in_stock", sa.Boolean()),
            sa.Column("last_checked_at", sa.DateTime(timezone=True)),
            sa.Column("next_check_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("status IN ('active','paused')", name="tracked_items_status"),
            sa.CheckConstraint("check_frequency BETWEEN 5 AND 10080", name="tracked_items_frequency"),
            sa.CheckConstraint("target_price IS NULL OR target_price >= 0", name="tracked_items_target_price"),
            sa.CheckConstraint("notify_channel IN ('email','push','system')", name="tracked_items_channel"),
            sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
            sa.UniqueConstraint("user_id", "normalized_url", name="uq_tracked_items_user_normalized_url"),
        )
        op.create_index("ix_tracked_items_user_id", "tracked_items", ["user_id"])
        op.create_index("ix_tracked_items_due", "tracked_items", ["status", "next_check_at"])
        return

    columns = {column["name"]: column for column in inspector.get_columns("tracked_items")}
    if "normalized_url" not in columns:
        op.add_column("tracked_items", sa.Column("normalized_url", sa.Text(), nullable=True))
        op.execute("UPDATE tracked_items SET normalized_url = url WHERE normalized_url IS NULL")
        op.alter_column("tracked_items", "normalized_url", nullable=False)
    op.alter_column("tracked_items", "url", type_=sa.Text(), existing_nullable=False)
    op.alter_column("tracked_items", "image_url", type_=sa.Text(), existing_nullable=True)
    op.alter_column("tracked_items", "in_stock", nullable=True, existing_type=sa.Boolean())

    constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("tracked_items")}
    if "tracked_items_user_id_url_key" in constraints:
        op.drop_constraint("tracked_items_user_id_url_key", "tracked_items", type_="unique")
    if "uq_tracked_items_user_normalized_url" not in constraints:
        op.create_unique_constraint(
            "uq_tracked_items_user_normalized_url",
            "tracked_items",
            ["user_id", "normalized_url"],
        )

    checks = {constraint["name"] for constraint in inspector.get_check_constraints("tracked_items")}
    if "tracked_items_notify_channel_check" in checks:
        op.execute(
            "ALTER TABLE tracked_items "
            "DROP CONSTRAINT tracked_items_notify_channel_check"
        )
    op.execute(
        "ALTER TABLE tracked_items "
        "ADD CONSTRAINT ck_tracked_items_notify_channel "
        "CHECK (notify_channel IN ('email','push','system'))"
    )


def downgrade() -> None:
    op.drop_constraint("uq_tracked_items_user_normalized_url", "tracked_items", type_="unique")
    op.drop_column("tracked_items", "normalized_url")
