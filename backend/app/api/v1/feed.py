import json
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
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
    ranked: bool = Query(True),  # smart ranking on by default (V4 Phase 2b)
    feedback: Optional[int] = Query(None, ge=-1, le=1),
    min_signal: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> FeedResponse:
    q = select(Article)

    # For authed users the state filters apply to *their* overlay, post-query
    user_state_filters = (is_read, is_bookmarked, feedback) if user else None
    if user:
        is_read = is_bookmarked = feedback = None

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
        from app.services.ranker import (
            _get_source_affinity, _get_topic_weights, rank_articles,
        )
        from app.services.relevance import apply_daily_caps, explain, interleave_by_group
        # Bound the candidate set: rank the newest 2000, not the whole table
        all_result = await db.execute(q.order_by(Article.published_at.desc()).limit(2000))
        all_items = list(all_result.scalars().all())

        window_days = TIME_RANGE_DAYS.get(time_range or "7d", 7)
        category_of = await _category_map(db)
        per_day = await _feed_density(db, user)

        # V7 anti-overwhelm: only the top-N most relevant items per source
        # category per day survive — the rest stay queryable via ranked=false
        capped = apply_daily_caps(
            all_items, per_day=per_day, window_days=window_days, category_of=category_of
        )
        # V8: display-time cross-source dedupe — the same story fetched via
        # two sources must never appear twice in one feed (app-feedback-v5)
        from app.services.dedupe import dedupe_cross_source
        capped = dedupe_cross_source(capped)

        user_id = user.id if user else None
        ranked_items = await rank_articles(capped, db, user_id=user_id)
        total = len(ranked_items)

        # Mix categories within each day unless the user already narrowed
        # to one source/category (a single column is then the point)
        if not source_id and not category:
            ranked_items = interleave_by_group(
                ranked_items, window_days=window_days, category_of=category_of
            )
        offset = (page - 1) * limit
        items = ranked_items[offset: offset + limit]

        # Visible relevance: match % + why, only for the page being returned
        topic_w = await _get_topic_weights(db, user_id)
        affinity = await _get_source_affinity(db, user_id)
        explanations = {
            a.id: explain(a, window_days, topic_weights=topic_w, source_affinity=affinity)
            for a in items
        }
    else:
        q = q.order_by(Article.published_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await db.execute(q)
        items = result.scalars().all()

    out_items = [ArticleOut.model_validate(a) for a in items]
    if ranked:
        for o in out_items:
            match, why = explanations.get(o.id, (None, None))
            o.relevance = match
            o.why = why or None

    if user:
        from app.services.user_state import overlay, state_map
        states = await state_map(db, user.id, [a.id for a in items])
        out_items = [
            ArticleOut(**overlay(o.model_dump(), states.get(o.id))) for o in out_items
        ]
        f_read, f_bm, f_fb = user_state_filters
        if f_read is not None:
            out_items = [o for o in out_items if o.is_read == f_read]
        if f_bm is not None:
            out_items = [o for o in out_items if o.is_bookmarked == f_bm]
        if f_fb is not None:
            out_items = [o for o in out_items if o.feedback == f_fb]

    return FeedResponse(
        items=out_items,
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


async def _category_map(db: AsyncSession) -> dict:
    result = await db.execute(select(Source.id, Source.category))
    return {sid: cat for sid, cat in result.all()}


async def _feed_density(db: AsyncSession, user) -> int:
    """Items per source category per day. User-namespaced pref first, then
    global, then the V7 default of 10."""
    from app.models.user_preference import UserPreference
    from app.services.relevance import DEFAULT_PER_SOURCE_PER_DAY

    keys = ([f"u:{user.id}:feed_density"] if user else []) + ["feed_density"]
    for key in keys:
        pref = await db.get(UserPreference, key)
        if pref:
            try:
                return max(1, min(50, int(json.loads(pref.value))))
            except Exception:
                continue
    return DEFAULT_PER_SOURCE_PER_DAY


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)) -> ArticleOut:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.is_read = True
    await db.commit()
    return ArticleOut.model_validate(article)
