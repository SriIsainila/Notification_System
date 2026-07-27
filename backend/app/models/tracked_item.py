from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrackedItem(Base):
    __tablename__ = "tracked_items"
    __table_args__ = (
        UniqueConstraint("user_id", "normalized_url", name="uq_tracked_items_user_normalized_url"),
    )

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    store_name: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    check_frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    change_scope: Mapped[str] = mapped_column(String(16), nullable=False, default="all", server_default="all")
    notify_channel: Mapped[str] = mapped_column(String(16), nullable=False, default="email")
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="LKR")
    in_stock: Mapped[bool | None] = mapped_column(Boolean)
    variants: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_check_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
