import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.database import AsyncSessionFactory
from app.models.item_change import ItemChange
from app.models.notification import Notification
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.schemas.scraper import ScrapedProduct
from app.services.scraper import scrape_product


Scraper = Callable[[str], Awaitable[ScrapedProduct]]


@dataclass
class WorkerResult:
    claimed: int = 0
    checked: int = 0
    changed: int = 0
    notifications: int = 0
    failed: int = 0


def serialize_value(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def detected_changes(item: TrackedItem, snapshot: ScrapedProduct) -> list[tuple[str, str | None, str | None]]:
    comparisons = (
        ("title", item.title, snapshot.title),
        ("price", item.current_price, snapshot.price),
        ("image", item.image_url, snapshot.image_url),
        ("stock", item.in_stock, snapshot.in_stock),
        ("variant", item.variants or {}, snapshot.variants),
    )
    return [
        (change_type, serialize_value(old_value), serialize_value(new_value))
        for change_type, old_value, new_value in comparisons
        if old_value != new_value
    ]


def notification_message(item: TrackedItem, change_type: str, old_value: str | None, new_value: str | None) -> str:
    title = item.title
    if change_type == "price":
        return f"{title} changed price from {old_value or 'unknown'} to {new_value or 'unknown'}."
    if change_type == "stock":
        status = "in stock" if new_value == "True" else "out of stock" if new_value == "False" else "unknown"
        return f"{title} stock status changed to {status}."
    return f"{title} changed its {change_type}."


def should_notify(change_scope: str, change_type: str) -> bool:
    return change_scope == "all" or change_scope == change_type


async def claim_due_items(session: AsyncSession) -> list[int]:
    now = datetime.now(UTC)
    result = await session.execute(
        select(TrackedItem)
        .where(
            TrackedItem.status == "active",
            TrackedItem.next_check_at <= now,
        )
        .order_by(TrackedItem.next_check_at)
        .limit(settings.scheduler_batch_size)
        .with_for_update(skip_locked=True)
    )
    items = list(result.scalars().all())
    for item in items:
        item.next_check_at = now + timedelta(minutes=item.check_frequency)
    await session.commit()
    return [item.item_id for item in items]


async def record_failure(item_id: int, message: str) -> None:
    async with AsyncSessionFactory() as session:
        item = await session.get(TrackedItem, item_id)
        if item is None:
            return
        item.failure_count += 1
        item.last_error = message[:2000]
        item.last_checked_at = datetime.now(UTC)
        delay_minutes = min(max(item.check_frequency, 5) * (2 ** min(item.failure_count, 5)), 1440)
        item.next_check_at = datetime.now(UTC) + timedelta(minutes=delay_minutes)
        await session.commit()


async def check_tracked_url(item_id: int, scraper: Scraper = scrape_product) -> tuple[int, int]:
    """Fetch one active tracked URL and persist any detected product changes.

    Returns the number of recorded changes and notifications. An unchanged
    snapshot only refreshes ``last_checked_at`` and clears prior failure state.
    """
    async with AsyncSessionFactory() as session:
        item = await session.get(TrackedItem, item_id)
        if item is None or item.status != "active":
            return 0, 0
        url = item.url

    try:
        snapshot = await scraper(url)
    except ApplicationError as error:
        await record_failure(item_id, error.message)
        raise
    except Exception as error:
        await record_failure(item_id, str(error))
        raise

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(TrackedItem)
            .where(TrackedItem.item_id == item_id, TrackedItem.status == "active")
            .with_for_update()
        )
        item = result.scalar_one_or_none()
        if item is None:
            return 0, 0

        now = datetime.now(UTC)
        is_baseline = item.content_hash is None
        if item.content_hash == snapshot.content_hash:
            item.last_checked_at = now
            item.failure_count = 0
            item.last_error = None
            await session.commit()
            return 0, 0

        changes = [] if is_baseline else detected_changes(item, snapshot)
        if snapshot.price is not None and (is_baseline or item.current_price != snapshot.price):
            session.add(
                PriceHistory(
                    item_id=item.item_id,
                    price=snapshot.price,
                    currency=snapshot.currency or item.currency,
                )
            )

        notification_count = 0
        for change_type, old_value, new_value in changes:
            notify = should_notify(item.change_scope, change_type)
            change = ItemChange(
                item_id=item.item_id,
                change_type=change_type,
                old_value=old_value,
                new_value=new_value,
                is_notified=notify,
            )
            session.add(change)
            await session.flush()
            if notify:
                notification_id = await session.scalar(
                    postgresql_insert(Notification)
                    .values(
                        user_id=item.user_id,
                        item_change_id=change.change_id,
                        message=notification_message(item, change_type, old_value, new_value),
                        channel=item.notify_channel,
                        delivery_status="pending",
                    )
                    .on_conflict_do_nothing(constraint="uq_notifications_change_channel")
                    .returning(Notification.notification_id)
                )
                if notification_id is not None:
                    notification_count += 1

        if snapshot.title:
            item.title = snapshot.title
        item.current_price = snapshot.price
        item.currency = snapshot.currency or item.currency
        item.image_url = snapshot.image_url
        item.in_stock = snapshot.in_stock
        item.variants = snapshot.variants
        item.content_hash = snapshot.content_hash
        item.last_checked_at = now
        item.failure_count = 0
        item.last_error = None
        await session.commit()
        return len(changes), notification_count


async def process_item(item_id: int, scraper: Scraper = scrape_product) -> tuple[int, int]:
    """Backward-compatible wrapper for checking one tracked URL."""
    return await check_tracked_url(item_id, scraper)


async def process_item_ids(item_ids: list[int], scraper: Scraper) -> WorkerResult:
    summary = WorkerResult(claimed=len(item_ids))
    semaphore = asyncio.Semaphore(settings.scheduler_concurrency)

    async def run_one(item_id: int) -> tuple[bool, int, int]:
        async with semaphore:
            try:
                change_count, notification_count = await check_tracked_url(item_id, scraper)
                return True, change_count, notification_count
            except Exception:
                return False, 0, 0

    results = await asyncio.gather(*(run_one(item_id) for item_id in item_ids))
    for succeeded, change_count, notification_count in results:
        if succeeded:
            summary.checked += 1
            summary.changed += change_count
            summary.notifications += notification_count
        else:
            summary.failed += 1
    return summary


async def process_active_items(scraper: Scraper = scrape_product) -> WorkerResult:
    """Check every active item once, isolating failures between URLs."""
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(TrackedItem.item_id)
            .where(TrackedItem.status == "active")
            .order_by(TrackedItem.item_id)
        )
        item_ids = list(result.scalars().all())
    return await process_item_ids(item_ids, scraper)


async def process_due_items(scraper: Scraper = scrape_product) -> WorkerResult:
    async with AsyncSessionFactory() as session:
        item_ids = await claim_due_items(session)
    return await process_item_ids(item_ids, scraper)
