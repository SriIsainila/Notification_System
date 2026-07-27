import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text

from app.core.config import settings
from app.database import engine
from app.services.tracking_worker import process_active_items


logger = logging.getLogger(__name__)
SCHEDULER_LOCK_ID = 6_142_093_517

scheduler = AsyncIOScheduler(timezone="UTC")


async def run_scheduler_cycle() -> None:
    async with engine.connect() as connection:
        acquired = await connection.scalar(
            text("SELECT pg_try_advisory_lock(:lock_id)"),
            {"lock_id": SCHEDULER_LOCK_ID},
        )
        if not acquired:
            logger.info("Scheduler cycle skipped because another instance holds the lock")
            return
        try:
            result = await process_active_items()
            logger.info(
                "Tracking cycle complete: claimed=%s checked=%s changed=%s notifications=%s failed=%s",
                result.claimed,
                result.checked,
                result.changed,
                result.notifications,
                result.failed,
            )
        finally:
            await connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": SCHEDULER_LOCK_ID},
            )


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        run_scheduler_cycle,
        trigger=IntervalTrigger(minutes=settings.tracker_interval_minutes),
        id="tracked-url-check",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
