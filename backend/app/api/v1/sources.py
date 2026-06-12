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
    name: Optional[str] = None
    url: Optional[str] = None


class SourceCreate(BaseModel):
    """V8 custom sources: rss = any feed URL, reddit = subreddit name,
    github = topic or org tracked via the Search API."""
    kind: str  # rss | reddit | github
    value: str  # feed URL / subreddit / topic-or-org
    name: Optional[str] = None
    priority: str = "medium"


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


_KIND_CONFIG = {
    "rss":    {"prefix": "custom-rss",    "category": "company", "access": "rss",
               "interval": "8h", "url": lambda v: v},
    "reddit": {"prefix": "custom-reddit", "category": "social",  "access": "api",
               "interval": "12h", "url": lambda v: f"https://www.reddit.com/r/{v}"},
    "github": {"prefix": "custom-github", "category": "github",  "access": "api",
               "interval": "daily", "url": lambda v: f"https://github.com/topics/{v}"},
}


@router.post("", response_model=SourceOut, status_code=201)
async def create_source(
    body: SourceCreate,
    db: AsyncSession = Depends(get_db),
) -> SourceOut:
    import re
    from datetime import date

    cfg = _KIND_CONFIG.get(body.kind)
    if not cfg:
        raise HTTPException(status_code=422, detail=f"unknown kind '{body.kind}'")
    value = body.value.strip().lstrip("r/").strip("/")
    if not value or (body.kind == "rss" and not value.startswith("http")):
        raise HTTPException(status_code=422, detail="invalid source value")

    slug = re.sub(r"[^a-z0-9]+", "-", value.lower().split("//")[-1])[:40].strip("-")
    source_id = f"{cfg['prefix']}-{slug}"
    if await db.get(Source, source_id):
        raise HTTPException(status_code=409, detail="source already exists")

    source = Source(
        id=source_id,
        name=body.name or (f"r/{value}" if body.kind == "reddit" else value),
        category=cfg["category"],
        url=cfg["url"](value),
        access=cfg["access"],
        enabled=True,
        priority=body.priority,
        refresh_interval=cfg["interval"],
        added_on=date.today(),
        signal_score=0.5,
        notes="user-added (V8)",
    )
    db.add(source)
    await db.commit()
    return SourceOut.model_validate(source)


@router.delete("/{source_id}", status_code=200)
async def disable_source(source_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Registry rule: sources are never deleted, only disabled with a note."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.enabled = False
    source.notes = (source.notes or "") + " | disabled by user"
    await db.commit()
    return {"id": source_id, "enabled": False}


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
    if body.name is not None:
        source.name = body.name[:256]
    if body.url is not None and body.url.startswith("http"):
        source.url = body.url
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
