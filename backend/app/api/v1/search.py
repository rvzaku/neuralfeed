from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.article import Article
from app.schemas.article import ArticleOut

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[ArticleOut])
async def search_articles(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> list[ArticleOut]:
    pattern = f"%{q}%"
    # V6 dynamic feed: a few extra candidates so read-item exclusion below still
    # returns a full page.
    stmt = (
        select(Article)
        .where(or_(Article.title.ilike(pattern), Article.summary.ilike(pattern)))
        .order_by(Article.published_at.desc())
        .limit(limit * 2)
    )
    result = await db.execute(stmt)
    articles = list(result.scalars().all())

    # V6: items the user has already opened drop out of search/Discover too, so
    # the whole app stays dynamic — not just the main feed.
    if user is not None:
        from app.api.v1.feed import _read_article_ids

        read_ids = await _read_article_ids(db, user.id)
        if read_ids:
            articles = [a for a in articles if a.id not in read_ids]
    articles = articles[:limit]

    # V9: relevance is visible on every card surface, not just the feed
    from app.services.relevance import explain
    out = []
    for a in articles:
        o = ArticleOut.model_validate(a)
        o.relevance, why = explain(a, window_days=30)
        o.why = why or None
        out.append(o)
    return out
