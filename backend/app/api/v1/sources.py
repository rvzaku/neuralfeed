from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.source import Source
from app.schemas.source import SourceOut

router = APIRouter(prefix="/sources", tags=["sources"])


class SourcePatch(BaseModel):
    enabled: Optional[bool] = None
    priority: Optional[str] = None


class SourceHealth(BaseModel):
    id: str
    name: str
    enabled: bool
    last_fetched_at: Optional[str] = None
    last_fetch_status: Optional[str] = None
    last_fetch_error: Optional[str] = None
    last_fetch_count: Optional[int] = None


@router.get("/health", response_model=list[SourceHealth])
async def sources_health(db: AsyncSession = Depends(get_db)) -> list[SourceHealth]:
    result = await db.execute(select(Source).order_by(Source.id))
    return [
        SourceHealth(
            id=s.id,
            name=s.name,
            enabled=s.enabled,
            last_fetched_at=s.last_fetched_at.isoformat() if s.last_fetched_at else None,
            last_fetch_status=s.last_fetch_status,
            last_fetch_error=s.last_fetch_error,
            last_fetch_count=s.last_fetch_count,
        )
        for s in result.scalars().all()
    ]


@router.get("", response_model=list[SourceOut])
async def list_sources(
    all: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[SourceOut]:
    q = select(Source).order_by(Source.priority)
    if not all:
        q = q.where(Source.enabled == True)
    result = await db.execute(q)
    return [SourceOut.model_validate(s) for s in result.scalars().all()]


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)) -> SourceOut:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceOut.model_validate(source)


@router.patch("/{source_id}", response_model=SourceOut)
async def patch_source(
    source_id: str,
    body: SourcePatch,
    db: AsyncSession = Depends(get_db),
) -> SourceOut:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if body.enabled is not None:
        source.enabled = body.enabled
    if body.priority is not None:
        source.priority = body.priority
    await db.commit()
    return SourceOut.model_validate(source)


async def _fetch_in_background(source_id: str) -> None:
    from app.core.database import AsyncSessionLocal
    from app.services.fetch_runner import run_fetch
    async with AsyncSessionLocal() as db:
        await run_fetch(source_id, db)


@router.post("/{source_id}/fetch", status_code=202)
async def trigger_fetch(
    source_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    background_tasks.add_task(_fetch_in_background, source_id)
    return {"queued": source_id}
