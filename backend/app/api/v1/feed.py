import hashlib
import json
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import cache
from app.core.config import settings
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
    include_read: bool = Query(False),  # V6 dynamic feed: viewed items drop out
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

    # `total` is the post-ranking survivor count in ranked mode (set below), so
    # the COUNT query is only needed for the raw paginated (ranked=false) path.
    total = 0

    if ranked:
        from app.services.ranker import _get_source_affinity, _get_topic_weights
        from app.services.relevance import explain

        window_days = TIME_RANGE_DAYS.get(time_range or "7d", 7)
        user_id = user.id if user else None
        per_day = await _feed_density(db, user)

        # The ranked ORDER (and cross-source buzz) is identical across the pages
        # of one scroll session, so cache it and let page 2..N just slice + load
        # 20 rows by id, instead of recomputing the whole pipeline each page.
        cache_key = _ranked_cache_key(
            user_id=user_id, source_id=source_id, category=category, topic=topic,
            time_range=time_range, min_signal=min_signal, include_read=include_read,
            per_day=per_day, state_filters=user_state_filters,
            anon_filters=None if user else (is_read, is_bookmarked, feedback),
        )
        cached = await cache.get_json(cache_key)
        if cached is not None:
            ordered_ids = cached["ids"]
            buzz = cached["buzz"]
            total = cached["total"]
        else:
            ordered_ids, buzz = await _compute_ranked_order(
                db, q, user, user_id, window_days, per_day,
                include_read, user_state_filters, source_id, category,
            )
            total = len(ordered_ids)
            await cache.set_json(
                cache_key,
                {"ids": ordered_ids, "buzz": buzz, "total": total},
                settings.feed_cache_ttl_seconds,
            )

        offset = (page - 1) * limit
        page_ids = ordered_ids[offset: offset + limit]
        items = await _load_in_order(db, page_ids)

        # Visible relevance: match % + why, only for the page being returned.
        topic_w = await _get_topic_weights(db, user_id)
        affinity = await _get_source_affinity(db, user_id)
        explanations = {
            a.id: explain(
                a, window_days, topic_weights=topic_w, source_affinity=affinity,
                mentions=buzz.get(a.id, 1),
            )
            for a in items
        }
    else:
        total_result = await db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar_one()
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
        from app.services.user_state import overlay_model, state_map
        states = await state_map(db, user.id, [a.id for a in items])
        # Mutate the three per-user fields on the existing models — no second
        # round-trip through model_dump()+model_validate() per item.
        for o in out_items:
            overlay_model(o, states.get(o.id))
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


def _ranked_cache_key(**parts) -> str:
    """Stable key over every input that changes the ranked ORDER. Page/limit are
    deliberately excluded — one cached order serves all pages of a scroll."""
    blob = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(blob.encode()).hexdigest()[:24]
    return f"feed:ranked:{digest}"


async def _compute_ranked_order(
    db: AsyncSession,
    q,
    user,
    user_id,
    window_days: int,
    per_day: int,
    include_read: bool,
    user_state_filters,
    source_id: Optional[str],
    category: Optional[str],
) -> "tuple[list[str], dict]":
    """The heavy pipeline: load candidates → per-day caps → cross-source dedupe
    → personalized rank → category interleave. Returns (ordered_ids, buzz)."""
    from app.services.dedupe import cross_source_buzz, dedupe_cross_source
    from app.services.ranker import (
        _get_muted_sources, _get_source_affinity, _get_topic_weights, rank_articles,
    )
    from app.services.relevance import (
        apply_daily_caps, interleave_by_group, score_map,
    )

    # Bound the candidate set: rank the newest 2000, not the whole table
    all_result = await db.execute(q.order_by(Article.published_at.desc()).limit(2000))
    all_items = list(all_result.scalars().all())

    # V6 dynamic feed: articles the user has already opened drop out, so the feed
    # always presents fresh material (unless they explicitly browse read items or
    # a bookmarked/feedback view, handled post-overlay).
    _f_read, _f_bm, _f_fb = user_state_filters or (None, None, None)
    if user and not include_read and _f_read is None and _f_bm is None and _f_fb is None:
        read_ids = await _read_article_ids(db, user.id)
        if read_ids:
            all_items = [a for a in all_items if a.id not in read_ids]

    category_of = await _category_map(db)

    # Score every candidate ONCE (each call parses the engagement JSON); the
    # caps + interleave passes below reuse this map instead of recomputing it.
    scores = score_map(all_items, window_days)

    # V7 anti-overwhelm: only the top-N most relevant items per source category
    # per day survive — the rest stay queryable via ranked=false.
    capped = apply_daily_caps(
        all_items, per_day=per_day, window_days=window_days,
        category_of=category_of, scores=scores,
    )
    # V8 display-time cross-source dedupe; count coverage BEFORE collapsing so the
    # survivor can show how many sources carry the story (traction).
    buzz = cross_source_buzz(capped)
    capped = dedupe_cross_source(capped)

    topic_w = await _get_topic_weights(db, user_id)
    affinity = await _get_source_affinity(db, user_id)
    muted = await _get_muted_sources(db, user_id)
    ranked_items = await rank_articles(
        capped, db, user_id=user_id, window_days=window_days,
        topic_weights=topic_w, source_affinity=affinity, muted_sources=muted,
    )

    # Mix categories within each day unless the query already narrowed to one
    # source/category (a single column is then the point).
    if not source_id and not category:
        ranked_items = interleave_by_group(
            ranked_items, window_days=window_days,
            category_of=category_of, scores=scores,
        )
    ids = [a.id for a in ranked_items]
    # Keep only the buzz entries for survivors, so the cached payload stays small.
    survivors = set(ids)
    return ids, {aid: n for aid, n in buzz.items() if aid in survivors and n > 1}


async def _load_in_order(db: AsyncSession, ids: list) -> list:
    """Load the given article ids and return them in the same order."""
    if not ids:
        return []
    result = await db.execute(select(Article).where(Article.id.in_(ids)))
    by_id = {a.id: a for a in result.scalars().all()}
    return [by_id[i] for i in ids if i in by_id]


async def _category_map(db: AsyncSession) -> dict:
    result = await db.execute(select(Source.id, Source.category))
    return {sid: cat for sid, cat in result.all()}


async def _read_article_ids(db: AsyncSession, user_id: str) -> set:
    """Ids the user has already opened (is_read) OR had on screen long enough to
    count as seen (is_seen) — both drop out of the dynamic feed so the user
    isn't shown the same items again."""
    from sqlalchemy import or_
    from app.models.user_article_state import UserArticleState

    result = await db.execute(
        select(UserArticleState.article_id).where(
            UserArticleState.user_id == user_id,
            or_(
                UserArticleState.is_read.is_(True),
                UserArticleState.is_seen.is_(True),
            ),
        )
    )
    return {row[0] for row in result.all()}


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


class SeenRequest(BaseModel):
    article_ids: list[str]


@router.post("/seen", status_code=204)
async def mark_articles_seen(
    body: SeenRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> None:
    """Record that these articles were on the user's screen, so they drop from
    the next dynamic-feed load. No-op for anonymous sessions (nothing to scope
    to). Capped so a single call can't bulk-suppress the whole table."""
    if user and body.article_ids:
        from app.services.user_state import mark_seen
        await mark_seen(db, user.id, body.article_ids[:200])


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)) -> ArticleOut:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    # KNOWN BUG (flagged, behavior intentionally unchanged for now): this mutates
    # the GLOBAL Article.is_read column, so in a multi-user deploy one user
    # opening an article marks it read for everyone. The correct fix routes
    # read-state through user_article_state (per-user overlay) — same issue in
    # articles.py. Deferred pending explicit go-ahead.
    article.is_read = True
    await db.commit()
    return ArticleOut.model_validate(article)
