"""In-process scheduled fetching via APScheduler.

Replaces Celery beat + Redis for the free-tier, single-user deployment.
Fetch logic itself lives in services/fetch_runner.py, so swapping back to
Celery later (Phase 3 scale-up) only changes the trigger, not the work.
"""

from datetime import datetime, timedelta, timezone

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import settings
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
    """Nominal interval clamped to refresh_max_hours so the feed never goes
    stale longer than the configured freshness window (V6: updated every
    3-4h). Sources that publish less often simply re-fetch into the dedupe
    layer — new items still surface within the window, repeats are dropped."""
    nominal = _INTERVAL_HOURS.get(refresh_interval, 24)
    return min(nominal, max(1, settings.refresh_max_hours))


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


_REENRICH_FLAG = "reenrich_70b_done"


async def _reenrich_job() -> None:
    """One-shot title quality upgrade (v0.3.3). Guarded by a DB flag so it runs
    once total — not on every free-tier restart — to avoid burning tokens
    re-rewriting titles that were already upgraded."""
    from app.models.user_preference import UserPreference
    from app.services.enricher import reenrich_recent

    async with AsyncSessionLocal() as db:
        if await db.get(UserPreference, _REENRICH_FLAG):
            return
        await reenrich_recent(db)
        db.add(UserPreference(key=_REENRICH_FLAG, value="true"))
        await db.commit()


async def _traction_job() -> None:
    from app.services.traction import enrich_editorial_traction
    async with AsyncSessionLocal() as db:
        await enrich_editorial_traction(db)


async def _discovery_job() -> None:
    from app.fetchers.account_discovery import discover_accounts
    async with AsyncSessionLocal() as db:
        await discover_accounts(db)


async def _digest_job() -> None:
    """Send the daily 'Today in AI' email to every user who opted in via the
    per-user `digest_email_enabled` preference. No-ops cleanly when email is
    unconfigured (see services.email.send_email)."""
    import json

    from app.models.user import User
    from app.models.user_preference import UserPreference
    from app.services.digest import build_digest
    from app.services.email import render_digest_email, send_email

    async with AsyncSessionLocal() as db:
        prefs = await db.execute(
            select(UserPreference).where(
                UserPreference.key.like("u:%:digest_email_enabled")
            )
        )
        sent = 0
        for pref in prefs.scalars().all():
            try:
                if not json.loads(pref.value):
                    continue
            except (json.JSONDecodeError, TypeError):
                continue
            user_id = pref.key.split(":", 2)[1]
            user = await db.get(User, user_id)
            if not user or not user.email:
                continue
            digest = await build_digest(db, user_id=user_id)
            if not digest.get("items"):
                continue
            html = render_digest_email(digest)
            if await send_email(user.email, "Your daily AI digest", html):
                sent += 1
        log.info("digest_job_complete", sent=sent)


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
        _enrich_job, "interval", hours=2,
        start_date=now + timedelta(minutes=10),
        id="enrich-slug-titles", replace_existing=True,
        max_instances=1, coalesce=True,
    )

    scheduler.add_job(
        _traction_job, "interval", hours=1,
        start_date=now + timedelta(minutes=5),
        id="editorial-traction", replace_existing=True,
        max_instances=1, coalesce=True,
    )

    scheduler.add_job(
        _reenrich_job, "date",
        run_date=now + timedelta(minutes=3),
        id="reenrich-70b-once", replace_existing=True,
        max_instances=1, coalesce=True,
    )

    scheduler.add_job(
        _digest_job, "cron",
        hour=max(0, min(23, settings.digest_send_hour_utc)),
        id="daily-digest-email", replace_existing=True,
        max_instances=1, coalesce=True,
    )

    scheduler.start()
    log.info("scheduler_started", jobs=len(sources) + 5)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
