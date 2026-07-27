import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.database import AsyncSessionFactory, engine
from app.main import app
from app.models.item_change import ItemChange
from app.models.notification import Notification
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.schemas.scraper import ScrapedProduct
from app.services.scheduler import scheduler, start_scheduler, stop_scheduler
from app.services.tracking_worker import process_due_items


def database_dsn() -> str:
    return settings.database_url.replace("+asyncpg", "")


def remove_test_user(email: str) -> None:
    with psycopg.connect(database_dsn()) as connection:
        connection.execute("DELETE FROM users WHERE email = %s", (email,))


async def force_due(item_id: int) -> None:
    async with AsyncSessionFactory() as session:
        item = await session.get(TrackedItem, item_id)
        assert item is not None
        item.next_check_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()


def snapshot(
    *,
    title: str,
    price: str,
    image: str,
    in_stock: bool,
    size: str,
    content_hash: str,
) -> ScrapedProduct:
    return ScrapedProduct(
        title=title,
        price=Decimal(price),
        currency="LKR",
        image_url=image,
        in_stock=in_stock,
        variants={"size": [size]},
        content_hash=content_hash,
        final_url="https://example.com/scheduled-product",
    )


@pytest.mark.asyncio
async def test_scheduler_baseline_changes_deduplication_and_pausing() -> None:
    email = f"scheduler-{uuid4().hex}@example.com"
    password = "correct-horse-battery"

    baseline = snapshot(
        title="Product A",
        price="100.00",
        image="https://example.com/a.jpg",
        in_stock=True,
        size="Small",
        content_hash="a" * 64,
    )
    changed = snapshot(
        title="Product B",
        price="80.00",
        image="https://example.com/b.jpg",
        in_stock=False,
        size="Large",
        content_hash="b" * 64,
    )

    async def scrape_baseline(_: str) -> ScrapedProduct:
        return baseline

    async def scrape_changed(_: str) -> ScrapedProduct:
        await asyncio.sleep(0.05)
        return changed

    async def scrape_failure(_: str) -> ScrapedProduct:
        raise ApplicationError("Website unavailable", status_code=502)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            register = await client.post(
                "/api/auth/register",
                json={"name": "Scheduler Tester", "email": email, "password": password},
            )
            assert register.status_code == 201, register.text
            login = await client.post(
                "/api/auth/token",
                json={"email": email, "password": password},
            )
            token = login.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post(
                "/api/products",
                headers=headers,
                json={
                    "url": "https://example.com/scheduled-product",
                    "notifyChannel": "system",
                },
            )
            assert created.status_code == 201, created.text
            item_id = created.json()["id"]
            assert created.json()["check_frequency"] == 5

            first = await process_due_items(scrape_baseline)
            assert first.claimed == 1
            assert first.checked == 1
            assert first.changed == 0
            assert first.notifications == 0

            await force_due(item_id)
            concurrent = await asyncio.gather(
                process_due_items(scrape_changed),
                process_due_items(scrape_changed),
            )
            assert sum(result.claimed for result in concurrent) == 1
            assert sum(result.checked for result in concurrent) == 1
            assert sum(result.changed for result in concurrent) == 5
            assert sum(result.notifications for result in concurrent) == 5

            await force_due(item_id)
            unchanged = await process_due_items(scrape_changed)
            assert unchanged.claimed == 1
            assert unchanged.changed == 0
            assert unchanged.notifications == 0

            async with AsyncSessionFactory() as session:
                change_count = await session.scalar(select(func.count()).select_from(ItemChange))
                notification_count = await session.scalar(select(func.count()).select_from(Notification))
                price_count = await session.scalar(select(func.count()).select_from(PriceHistory))
                statuses = list((await session.execute(select(Notification.delivery_status))).scalars())
                assert change_count == 5
                assert notification_count == 5
                assert price_count == 2
                assert statuses == ["pending"] * 5

            await force_due(item_id)
            failed = await process_due_items(scrape_failure)
            assert failed.claimed == 1
            assert failed.failed == 1
            async with AsyncSessionFactory() as session:
                item = await session.get(TrackedItem, item_id)
                assert item is not None
                assert item.failure_count == 1
                assert item.last_error == "Website unavailable"
                assert item.next_check_at > datetime.now(UTC) + timedelta(minutes=9)

            disabled = await client.post(f"/api/products/{item_id}/disable", headers=headers)
            assert disabled.status_code == 200
            await force_due(item_id)
            paused = await process_due_items(scrape_changed)
            assert paused.claimed == 0
    finally:
        await engine.dispose()
        remove_test_user(email)


@pytest.mark.asyncio
async def test_apscheduler_job_runs_every_minute() -> None:
    start_scheduler()
    try:
        job = scheduler.get_job("tracked-url-check")
        assert job is not None
        assert job.trigger.interval.total_seconds() == settings.tracker_interval_minutes * 60
        assert job.max_instances == 1
        assert job.coalesce is True
    finally:
        stop_scheduler()
