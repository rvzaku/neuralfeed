from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.services.story_clusterer import get_stories, get_story_detail

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("")
async def list_stories(
    days: int = Query(default=1, ge=1, le=30),
    limit: int = Query(default=12, ge=1, le=50),
    unread_only: bool = True,
    topic: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await get_stories(db, days=days, limit=limit, unread_only=unread_only, topic=topic)


@router.get("/{story_id}")
async def story_detail(
    story_id: str,
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Stories are computed on demand; recompute over a wide window and look up.
    digest = await get_stories(db, days=days, limit=500, unread_only=False)
    story = next((s for s in digest["stories"] if s["id"] == story_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found (may have aged out)")
    detail = await get_story_detail(db, story["article_ids"])
    return {**story, **detail}
