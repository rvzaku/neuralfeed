"""One-shot historical backfill: pull a multi-week window from every source
whose API supports date-windowed or popularity-sorted lookback (V7).

Sources without lookback (RSS feeds, scrapes) just run a normal fetch via
BaseFetcher.backfill()'s default. Runs sequentially with low parallelism —
this is a rare admin action, not the hot path, and several upstreams
(Reddit, arXiv, GitHub search) are rate-touchy.
"""

import asyncio
from typing import Callable, Optional

import structlog
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.time import utcnow
from app.fetchers.registry import is_fetchable, resolve_fetcher
from app.models.source import Source
from app.services.ingest import ingest_items

log = structlog.get_logger()

_progress: dict = {"running": False, "total": 0, "done": 0, "inserted": 0,
                   "errors": [], "started_at": None}
# Lazy: a module-level asyncio.Lock binds to the import-time loop on py3.9
_run_lock: "asyncio.Lock | None" = None


def get_backfill_progress() -> dict:
    return dict(_progress)


async def backfill_all(
    days: int = 30,
    session_factory: Optional[Callable] = None,
    concurrency: int = 2,
) -> dict:
    global _run_lock
    if _run_lock is None:
        _run_lock = asyncio.Lock()
    if _run_lock.locked():
        log.info("backfill_already_running")
        return get_backfill_progress()

    factory = session_factory or AsyncSessionLocal

    async with _run_lock:
        async with factory() as db:
            result = await db.execute(
                select(Source.id, Source.url).where(Source.enabled == True)  # noqa: E712
            )
            sources = [(sid, url) for sid, url in result.all() if is_fetchable(sid)]
            source_ids = [sid for sid, _ in sources]
            url_of = dict(sources)

        # hf-papers last: its traction boost needs the arxiv articles in place
        source_ids.sort(key=lambda sid: sid == "hf-papers")

        _progress.update(running=True, total=len(source_ids), done=0, inserted=0,
                         errors=[], started_at=utcnow().isoformat())
        sem = asyncio.Semaphore(concurrency)

        async def _one(source_id: str) -> None:
            async with sem:
                try:
                    fetcher = resolve_fetcher(source_id, url=url_of.get(source_id))
                    if fetcher is None:
                        return
                    result = await fetcher.backfill(days=days)
                    if not result.ok:
                        _progress["errors"].append({"source_id": source_id, "error": result.error[:200]})
                        return
                    async with factory() as db:
                        inserted = await ingest_items(result.items, source_id, db)
                        _progress["inserted"] += inserted
                except Exception as exc:
                    log.error("backfill_source_crashed", source_id=source_id, error=str(exc))
                    _progress["errors"].append({"source_id": source_id, "error": str(exc)[:200]})
                finally:
                    _progress["done"] += 1

        await asyncio.gather(*(_one(sid) for sid in source_ids))
        _progress["running"] = False
        log.info("backfill_complete", total=_progress["total"],
                 inserted=_progress["inserted"], errors=len(_progress["errors"]))
        return get_backfill_progress()
