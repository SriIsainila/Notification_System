"""Create or upgrade the users table for authentication.

Revision ID: 20260722_01
Revises:
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260722_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "users" not in inspector.get_table_names():
        op.create_table(
            "users",
            sa.Column("user_id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("full_name", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=254), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=20), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint("email", name="uq_users_email"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=False)
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "password" in columns and "password_hash" not in columns:
        op.alter_column("users", "password", new_column_name="password_hash")
    if "is_active" not in columns:
        op.add_column(
            "users",
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        )

    indexes = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_email" not in indexes:
        op.create_index("ix_users_email", "users", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
