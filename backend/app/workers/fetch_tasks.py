import asyncio
import structlog
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.fetchers.registry import FETCHER_MAP
from app.fetchers.rss import RSS_SOURCES
from app.services.fetch_runner import run_fetch

log = structlog.get_logger()


async def _run_fetch(source_id: str) -> int:
    async with AsyncSessionLocal() as db:
        return await run_fetch(source_id, db)


@celery_app.task(name="app.workers.fetch_tasks.fetch_source", bind=True, max_retries=3)
def fetch_source(self, source_id: str) -> int:
    try:
        return asyncio.run(_run_fetch(source_id))
    except Exception as exc:
        log.error("fetch_task_error", source_id=source_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.workers.fetch_tasks.fetch_all_rss")
def fetch_all_rss() -> dict:
    results = {}
    for source_id in RSS_SOURCES:
        results[source_id] = asyncio.run(_run_fetch(source_id))
    return results


@celery_app.task(name="app.workers.fetch_tasks.discover_accounts")
def discover_accounts_task() -> dict:
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.fetchers.account_discovery import discover_accounts
        async with AsyncSessionLocal() as db:
            upserted = await discover_accounts(db)
        return {"upserted": upserted}
    return asyncio.run(_run())


@celery_app.task(name="app.workers.fetch_tasks.fetch_all")
def fetch_all() -> dict:
    results = {}
    for source_id in FETCHER_MAP:
        results[source_id] = asyncio.run(_run_fetch(source_id))
    return results
