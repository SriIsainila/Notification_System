from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.models.item_change import ItemChange
from app.models.notification import Notification
from app.models.tracked_item import TrackedItem
from app.schemas.notification import NotificationRead


def notification_select(user_id: int):
    return (
        select(
            Notification.notification_id,
            Notification.message,
            Notification.channel,
            Notification.delivery_status,
            Notification.is_read,
            Notification.sent_at,
            Notification.created_at,
            ItemChange.change_type,
            ItemChange.item_id,
            TrackedItem.title.label("item_title"),
        )
        .outerjoin(ItemChange, ItemChange.change_id == Notification.item_change_id)
        .outerjoin(TrackedItem, TrackedItem.item_id == ItemChange.item_id)
        .where(Notification.user_id == user_id)
    )


def row_to_schema(row) -> NotificationRead:
    return NotificationRead(
        id=row.notification_id,
        message=row.message,
        channel=row.channel,
        delivery_status=row.delivery_status,
        is_read=row.is_read,
        sent_at=row.sent_at,
        created_at=row.created_at,
        change_type=row.change_type,
        item_id=row.item_id,
        item_title=row.item_title,
    )


async def list_notifications(
    session: AsyncSession,
    user_id: int,
    *,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[NotificationRead]:
    statement = notification_select(user_id)
    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))
    result = await session.execute(
        statement.order_by(Notification.created_at.desc(), Notification.notification_id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [row_to_schema(row) for row in result]


async def mark_notification_read(session: AsyncSession, user_id: int, notification_id: int) -> Notification:
    result = await session.execute(
        update(Notification)
        .where(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id,
        )
        .values(is_read=True)
        .returning(Notification)
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        await session.rollback()
        raise ApplicationError("Notification not found", status_code=404)
    await session.commit()
    return notification


async def mark_all_notifications_read(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await session.commit()
    return result.rowcount


async def delete_notification(session: AsyncSession, user_id: int, notification_id: int) -> None:
    result = await session.execute(
        delete(Notification).where(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id,
        )
    )
    if result.rowcount == 0:
        await session.rollback()
        raise ApplicationError("Notification not found", status_code=404)
    await session.commit()
