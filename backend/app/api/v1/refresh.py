from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/refresh", tags=["refresh"])


async def _refresh_all() -> None:
    from app.core.database import AsyncSessionLocal
    from app.fetchers.registry import FETCHER_MAP
    from app.models.source import Source
    from app.services.fetch_runner import run_fetch

    async with AsyncSessionLocal() as db:
        for source_id in FETCHER_MAP:
            source = await db.get(Source, source_id)
            if source and not source.enabled:
                continue
            await run_fetch(source_id, db)


@router.post("", status_code=202)
async def refresh_all(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_refresh_all)
    return {"queued": True, "message": "Refresh started for all enabled sources"}
