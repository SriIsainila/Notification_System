"""Add scheduler snapshots, change history, and notification deduplication.

Revision ID: 20260722_03
Revises: 20260722_02
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260722_03"
down_revision: str | None = "20260722_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    tracked_columns = {column["name"] for column in inspector.get_columns("tracked_items")}
    if "variants" not in tracked_columns:
        op.add_column(
            "tracked_items",
            sa.Column(
                "variants",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'{}'::jsonb"),
                nullable=False,
            ),
        )
    if "content_hash" not in tracked_columns:
        op.add_column("tracked_items", sa.Column("content_hash", sa.String(64)))
        op.create_index("ix_tracked_items_content_hash", "tracked_items", ["content_hash"])
    if "failure_count" not in tracked_columns:
        op.add_column(
            "tracked_items",
            sa.Column("failure_count", sa.Integer(), server_default="0", nullable=False),
        )
    if "last_error" not in tracked_columns:
        op.add_column("tracked_items", sa.Column("last_error", sa.Text()))
    op.alter_column(
        "tracked_items",
        "check_frequency",
        existing_type=sa.Integer(),
        server_default="5",
        existing_nullable=False,
    )

    if "price_history" not in tables:
        op.create_table(
            "price_history",
            sa.Column("price_id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("item_id", sa.BigInteger(), nullable=False),
            sa.Column("price", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(10), server_default="LKR", nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["item_id"], ["tracked_items.item_id"], ondelete="CASCADE"),
        )
        op.create_index("ix_price_history_item_id", "price_history", ["item_id"])
    else:
        price_columns = {column["name"] for column in inspector.get_columns("price_history")}
        price_indexes = {index["name"] for index in inspector.get_indexes("price_history")}
        if "price_history_one_current_idx" in price_indexes:
            op.drop_index("price_history_one_current_idx", table_name="price_history")
        if "is_current" in price_columns:
            op.drop_column("price_history", "is_current")

    if "item_changes" not in tables:
        op.create_table(
            "item_changes",
            sa.Column("change_id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("item_id", sa.BigInteger(), nullable=False),
            sa.Column("change_type", sa.String(16), nullable=False),
            sa.Column("old_value", sa.Text()),
            sa.Column("new_value", sa.Text()),
            sa.Column("change_detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("is_notified", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.CheckConstraint(
                "change_type IN ('price','stock','title','image','variant','other')",
                name="item_changes_type",
            ),
            sa.ForeignKeyConstraint(["item_id"], ["tracked_items.item_id"], ondelete="CASCADE"),
        )
        op.create_index("ix_item_changes_item_id", "item_changes", ["item_id"])
    else:
        change_checks = {constraint["name"] for constraint in inspector.get_check_constraints("item_changes")}
        if "item_changes_change_type_check" in change_checks:
            op.execute("ALTER TABLE item_changes DROP CONSTRAINT item_changes_change_type_check")
        op.execute(
            "ALTER TABLE item_changes ADD CONSTRAINT ck_item_changes_change_type "
            "CHECK (change_type IN ('price','stock','title','image','variant','other'))"
        )

    if "notifications" not in tables:
        op.create_table(
            "notifications",
            sa.Column("notification_id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("item_change_id", sa.BigInteger()),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("channel", sa.String(16), nullable=False),
            sa.Column("delivery_status", sa.String(16), server_default="pending", nullable=False),
            sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("sent_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("channel IN ('email','push','system')", name="notifications_channel"),
            sa.CheckConstraint(
                "delivery_status IN ('pending','processing','sent','delivered','failed')",
                name="notifications_delivery_status",
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["item_change_id"], ["item_changes.change_id"], ondelete="SET NULL"),
            sa.UniqueConstraint("item_change_id", "channel", name="uq_notifications_change_channel"),
        )
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    else:
        notification_columns = {column["name"] for column in inspector.get_columns("notifications")}
        if "delivery_status" not in notification_columns:
            op.add_column(
                "notifications",
                sa.Column("delivery_status", sa.String(16), server_default="pending", nullable=False),
            )
        notification_checks = {
            constraint["name"] for constraint in inspector.get_check_constraints("notifications")
        }
        if "notifications_channel_check" in notification_checks:
            op.execute("ALTER TABLE notifications DROP CONSTRAINT notifications_channel_check")
        op.execute(
            "ALTER TABLE notifications ADD CONSTRAINT ck_notifications_channel "
            "CHECK (channel IN ('email','push','system'))"
        )
        op.execute(
            "ALTER TABLE notifications ADD CONSTRAINT ck_notifications_delivery_status "
            "CHECK (delivery_status IN ('pending','processing','sent','delivered','failed'))"
        )
        unique_constraints = {
            constraint["name"] for constraint in inspector.get_unique_constraints("notifications")
        }
        if "uq_notifications_change_channel" not in unique_constraints:
            op.create_unique_constraint(
                "uq_notifications_change_channel",
                "notifications",
                ["item_change_id", "channel"],
            )


def downgrade() -> None:
    op.drop_constraint("uq_notifications_change_channel", "notifications", type_="unique")
    op.drop_column("notifications", "delivery_status")
    op.drop_column("tracked_items", "last_error")
    op.drop_column("tracked_items", "failure_count")
    op.drop_index("ix_tracked_items_content_hash", table_name="tracked_items")
    op.drop_column("tracked_items", "content_hash")
    op.drop_column("tracked_items", "variants")
