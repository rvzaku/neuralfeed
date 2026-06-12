from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.services.story_clusterer import get_stories, get_story_detail

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("")
async def list_stories(
    days: int = Query(default=1, ge=1, le=30),
    limit: int = Query(default=12, ge=1, le=50),
    unread_only: bool = True,
    topic: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    read_ids = await _user_read_ids(db, user) if user else None
    return await get_stories(
        db, days=days, limit=limit, unread_only=unread_only, topic=topic, read_ids=read_ids
    )


@router.get("/{story_id}")
async def story_detail(
    story_id: str,
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    # Stories are computed on demand; recompute over a wide window and look up.
    read_ids = await _user_read_ids(db, user) if user else None
    digest = await get_stories(db, days=days, limit=500, unread_only=False, read_ids=read_ids)
    story = next((s for s in digest["stories"] if s["id"] == story_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found (may have aged out)")
    states = None
    if user:
        from app.services.user_state import state_map
        states = await state_map(db, user.id, story["article_ids"])
    detail = await get_story_detail(db, story["article_ids"], states=states)
    return {**story, **detail}


async def _user_read_ids(db: AsyncSession, user) -> set:
    from sqlalchemy import select
    from app.models.user_article_state import UserArticleState
    result = await db.execute(
        select(UserArticleState.article_id).where(
            UserArticleState.user_id == user.id, UserArticleState.is_read.is_(True)
        )
    )
    return set(result.scalars().all())
