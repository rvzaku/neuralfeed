"""In-process scheduled fetching via APScheduler.

Replaces Celery beat + Redis for the free-tier, single-user deployment.
Fetch logic itself lives in services/fetch_runner.py, so swapping back to
Celery later (Phase 3 scale-up) only changes the trigger, not the work.
"""

from datetime import datetime, timedelta, timezone

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.source import Source
from app.services.fetch_runner import run_fetch

log = structlog.get_logger()

scheduler = AsyncIOScheduler()

_INTERVAL_HOURS = {
    "4h": 4, "6h": 6, "8h": 8, "12h": 12,
    "daily": 24, "weekly": 168,
}


def _hours_for(refresh_interval: str) -> int:
    return _INTERVAL_HOURS.get(refresh_interval, 24)


async def _fetch_job(source_id: str) -> None:
    async with AsyncSessionLocal() as db:
        source = await db.get(Source, source_id)
        if not source or not source.enabled:
            return
        # Skip if fetched recently (cheap resume after restarts: cold starts
        # re-register jobs, but sources that already ran shouldn't re-fetch)
        interval_h = _hours_for(source.refresh_interval)
        if source.last_fetched_at and (
            datetime.now(timezone.utc).replace(tzinfo=None) - source.last_fetched_at
        ) < timedelta(hours=interval_h * 0.5):
            return
        source.fetch_attempted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        await run_fetch(source_id, db)


async def _enrich_job() -> None:
    from app.services.enricher import enrich_slug_titles
    async with AsyncSessionLocal() as db:
        await enrich_slug_titles(db)


async def _discovery_job() -> None:
    from app.fetchers.account_discovery import discover_accounts
    async with AsyncSessionLocal() as db:
        await discover_accounts(db)


async def start_scheduler() -> None:
    """Register one interval job per enabled source, staggered so a cold
    start doesn't fire every fetcher at once."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Source).where(Source.enabled == True))
        sources = result.scalars().all()

    now = datetime.now(timezone.utc)
    for i, source in enumerate(sources):
        scheduler.add_job(
            _fetch_job,
            "interval",
            hours=_hours_for(source.refresh_interval),
            start_date=now + timedelta(minutes=2 + i),  # stagger one minute apart
            args=[source.id],
            id=f"fetch:{source.id}",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    scheduler.add_job(
        _discovery_job, "interval", days=7,
        start_date=now + timedelta(hours=1),
        id="discover-accounts", replace_existing=True,
    )

    scheduler.add_job(
        _enrich_job, "interval", hours=1,
        start_date=now + timedelta(minutes=10),
        id="enrich-slug-titles", replace_existing=True,
        max_instances=1, coalesce=True,
    )

    scheduler.start()
    log.info("scheduler_started", jobs=len(sources) + 2)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
