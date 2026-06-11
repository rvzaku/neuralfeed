from fastapi import APIRouter, BackgroundTasks

from app.services.refresh_orchestrator import get_progress, refresh_all

router = APIRouter(prefix="/refresh", tags=["refresh"])


@router.post("", status_code=202)
async def trigger_refresh(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(refresh_all)
    return {"queued": True, "message": "Refresh started for all enabled sources"}


@router.get("/status")
async def refresh_status() -> dict:
    return get_progress()
