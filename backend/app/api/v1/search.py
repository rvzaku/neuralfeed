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
    articles = list(result.scalars().all())

    # V9: relevance is visible on every card surface, not just the feed
    from app.services.relevance import explain
    out = []
    for a in articles:
        o = ArticleOut.model_validate(a)
        o.relevance, why = explain(a, window_days=30)
        o.why = why or None
        out.append(o)
    return out
