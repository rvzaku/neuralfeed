from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.services.digest import DEFAULT_LIMIT, build_digest

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("")
async def get_digest(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    """The in-app 'Today in AI' digest: the top recent stories, ranked with the
    same pipeline as the feed (and the requesting user's learned taste)."""
    return await build_digest(db, user_id=user.id if user else None, limit=limit)
