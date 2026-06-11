from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.time import utcnow
from app.models.article import Article
from app.models.source import Source
from app.schemas.article import ArticleOut, FeedResponse

router = APIRouter(prefix="/feed", tags=["feed"])

TIME_RANGE_DAYS = {"1d": 1, "3d": 3, "7d": 7, "30d": 30}


@router.get("", response_model=FeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source_id: Optional[str] = None,
    category: Optional[str] = None,
    topic: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_bookmarked: Optional[bool] = None,
    time_range: Optional[str] = Query(None, pattern="^(1d|3d|7d|30d)$"),
    ranked: bool = Query(False),
    feedback: Optional[int] = Query(None, ge=-1, le=1),
    min_signal: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
) -> FeedResponse:
    q = select(Article)

    # Join Source once if any Source-column filter is active
    needs_source_join = bool(category or min_signal is not None)
    if needs_source_join:
        q = q.join(Source, Article.source_id == Source.id)

    if source_id:
        q = q.where(Article.source_id == source_id)
    if category:
        q = q.where(Source.category == category)
    if is_read is not None:
        q = q.where(Article.is_read == is_read)
    if is_bookmarked is not None:
        q = q.where(Article.is_bookmarked == is_bookmarked)
    if time_range and time_range in TIME_RANGE_DAYS:
        cutoff = utcnow() - timedelta(days=TIME_RANGE_DAYS[time_range])
        q = q.where(Article.published_at >= cutoff)
    if topic:
        q = q.where(Article.topic_tags.contains([topic]))
    if feedback is not None:
        q = q.where(Article.feedback == feedback)
    if min_signal is not None:
        q = q.where(Source.signal_score >= min_signal)

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    if ranked:
        from app.services.ranker import rank_articles
        all_result = await db.execute(q)
        all_items = list(all_result.scalars().all())
        ranked_items = await rank_articles(all_items, db)
        offset = (page - 1) * limit
        items = ranked_items[offset: offset + limit]
    else:
        q = q.order_by(Article.published_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await db.execute(q)
        items = result.scalars().all()

    return FeedResponse(
        items=[ArticleOut.model_validate(a) for a in items],
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)) -> ArticleOut:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.is_read = True
    await db.commit()
    return ArticleOut.model_validate(article)
