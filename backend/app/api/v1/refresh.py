from fastapi import APIRouter, BackgroundTasks, Query

from app.services.backfill import backfill_all, get_backfill_progress
from app.services.refresh_orchestrator import get_progress, refresh_all

router = APIRouter(prefix="/refresh", tags=["refresh"])


@router.post("", status_code=202)
async def trigger_refresh(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(refresh_all)
    return {"queued": True, "message": "Refresh started for all enabled sources"}


@router.get("/status")
async def refresh_status() -> dict:
    return get_progress()


@router.post("/backfill", status_code=202)
async def trigger_backfill(
    background_tasks: BackgroundTasks,
    days: int = Query(30, ge=1, le=90),
) -> dict:
    background_tasks.add_task(backfill_all, days)
    return {"queued": True, "message": f"Backfill started for the last {days} days"}


@router.get("/backfill/status")
async def backfill_status() -> dict:
    return get_backfill_progress()
