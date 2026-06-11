from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.article import Article
from app.schemas.article import ArticleOut

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[ArticleOut])
async def search_articles(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[ArticleOut]:
    pattern = f"%{q}%"
    stmt = (
        select(Article)
        .where(or_(Article.title.ilike(pattern), Article.summary.ilike(pattern)))
        .order_by(Article.published_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [ArticleOut.model_validate(a) for a in result.scalars().all()]
