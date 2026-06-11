from fastapi import APIRouter
from app.workers.fetch_tasks import fetch_all

router = APIRouter(prefix="/refresh", tags=["refresh"])


@router.post("", status_code=202)
async def refresh_all() -> dict:
    fetch_all.delay()
    return {"queued": True, "message": "Fetch tasks enqueued for all enabled sources"}
