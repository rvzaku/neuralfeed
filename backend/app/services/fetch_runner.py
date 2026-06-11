"""Run a fetcher for a source, ingest its items, and record fetch health
on the Source row. Single entry point used by workers, the scheduler,
manual refresh, and the health-check script."""

from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.fetchers.registry import FETCHER_MAP
from app.models.source import Source
from app.services.ingest import ingest_items

log = structlog.get_logger()


async def _record_health(
    db: AsyncSession, source_id: str, status: str, error: Optional[str], count: int
) -> None:
    source = await db.get(Source, source_id)
    if not source:
        return
    source.last_fetch_status = status
    source.last_fetch_error = error[:1000] if error else None
    source.last_fetch_count = count
    if status == "ok":
        source.last_fetched_at = utcnow()
    await db.commit()


async def run_fetch(source_id: str, db: AsyncSession) -> int:
    """Fetch one source, ingest, record health. Returns items inserted."""
    factory = FETCHER_MAP.get(source_id)
    if not factory:
        log.warning("unknown_source", source_id=source_id)
        await _record_health(db, source_id, "error", "no fetcher registered", 0)
        return 0

    try:
        result = await factory().fetch()
    except Exception as exc:  # fetcher bugs must not take the caller down
        log.error("fetch_crashed", source_id=source_id, error=str(exc))
        await _record_health(db, source_id, "error", str(exc), 0)
        return 0

    if not result.ok:
        log.error("fetch_failed", source_id=source_id, error=result.error)
        await _record_health(db, source_id, "error", result.error, 0)
        return 0

    inserted = await ingest_items(result.items, source_id, db)
    await _record_health(db, source_id, "ok", None, len(result.items))
    return inserted
