"""Full-refresh orchestration: batched concurrency, per-source error isolation,
and crash-resumable ordering.

Sources are processed least-recently-attempted first, and the cursor
(`Source.fetch_attempted_at`) is stamped *before* fetching — so if the host
restarts mid-refresh, the next run picks up the sources that never got a turn
instead of restarting from the top of the list.
"""

import asyncio
from typing import Callable, Optional

import structlog
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.time import utcnow
from app.fetchers.registry import FETCHER_MAP
from app.models.source import Source
from app.services.fetch_runner import run_fetch

log = structlog.get_logger()

_progress: dict = {"running": False, "total": 0, "done": 0, "errors": [], "started_at": None}
_run_lock = asyncio.Lock()


def get_progress() -> dict:
    return dict(_progress)


async def refresh_all(
    session_factory: Optional[Callable] = None,
    concurrency: int = 3,
) -> dict:
    """Fetch every enabled source with a registered fetcher. Returns progress."""
    if _run_lock.locked():
        log.info("refresh_already_running")
        return get_progress()

    factory = session_factory or AsyncSessionLocal

    async with _run_lock:
        async with factory() as db:
            result = await db.execute(
                select(Source.id)
                .where(Source.enabled == True)  # noqa: E712
                .order_by(Source.fetch_attempted_at.asc().nulls_first())
            )
            source_ids = [sid for (sid,) in result.all() if sid in FETCHER_MAP]

        _progress.update(
            running=True, total=len(source_ids), done=0, errors=[], started_at=utcnow().isoformat()
        )
        sem = asyncio.Semaphore(concurrency)

        async def _one(source_id: str) -> None:
            async with sem:
                try:
                    async with factory() as db:
                        source = await db.get(Source, source_id)
                        if source is None or not source.enabled:
                            return
                        source.fetch_attempted_at = utcnow()
                        await db.commit()
                        await run_fetch(source_id, db)
                except Exception as exc:  # isolation: one source never stops the rest
                    log.error("refresh_source_crashed", source_id=source_id, error=str(exc))
                    _progress["errors"].append({"source_id": source_id, "error": str(exc)[:200]})
                finally:
                    _progress["done"] += 1

        await asyncio.gather(*(_one(sid) for sid in source_ids))
        _progress["running"] = False
        log.info("refresh_complete", total=_progress["total"], errors=len(_progress["errors"]))
        return get_progress()
