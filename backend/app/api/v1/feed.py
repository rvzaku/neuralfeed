import hashlib
import json
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, String, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import cache
from app.core.config import settings
from app.core.deps import get_current_user, get_db, is_guest
from app.core.time import utcnow
from app.models.article import Article
from app.models.source import Source
from app.schemas.article import ArticleOut, FeedResponse

router = APIRouter(prefix="/feed", tags=["feed"])

TIME_RANGE_DAYS = {"1d": 1, "3d": 3, "7d": 7, "30d": 30, "90d": 90, "365d": 365}


def _csv(value: Optional[str]) -> list[str]:
    """Split a comma-joined multi-select param ("llm,ai-agents") into a clean list.
    Single values and empty/None both behave sanely."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


@router.get("", response_model=FeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source_id: Optional[str] = None,
    category: Optional[str] = None,
    topic: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_bookmarked: Optional[bool] = None,
    time_range: Optional[str] = Query(None, pattern="^(1d|3d|7d|30d|90d|365d)$"),
    ranked: bool = Query(True),  # smart ranking on by default (V4 Phase 2b)
    feedback: Optional[int] = Query(None, ge=-1, le=1),
    min_signal: Optional[float] = Query(None, ge=0.0, le=1.0),
    include_read: bool = Query(False),  # V6 dynamic feed: viewed items drop out
    # V7-6: the Feed is a finite ranked shortlist capped to feed-density; Discover
    # passes cap_to_density=false to page through the full ranked set ("Show more").
    cap_to_density: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> FeedResponse:
    q = select(Article)

    # For authed users the state filters apply to *their* overlay, post-query
    user_state_filters = (is_read, is_bookmarked, feedback) if user else None
    if user:
        is_read = is_bookmarked = feedback = None

    # Multi-select: source_id / category / topic accept comma-joined values.
    source_ids = _csv(source_id)
    categories = _csv(category)
    topics = _csv(topic)

    # Join Source once if any Source-column filter is active
    needs_source_join = bool(categories or min_signal is not None)
    if needs_source_join:
        q = q.join(Source, Article.source_id == Source.id)

    if source_ids:
        q = q.where(Article.source_id.in_(source_ids))
    if categories:
        q = q.where(Source.category.in_(categories))
    if is_read is not None:
        q = q.where(Article.is_read == is_read)
    if is_bookmarked is not None:
        q = q.where(Article.is_bookmarked == is_bookmarked)
    if time_range and time_range in TIME_RANGE_DAYS:
        cutoff = utcnow() - timedelta(days=TIME_RANGE_DAYS[time_range])
        q = q.where(Article.published_at >= cutoff)
    if topics:
        # topic_tags is a generic JSON array column; SQLAlchemy's `.contains()`
        # degrades to a LIKE on the *whole* serialized list (e.g. '%["llm"]%'),
        # which only matches articles where the topic is the SOLE tag and silently
        # drops every multi-tag article. Match each quoted slug as a substring of
        # the JSON text instead — portable across SQLite and Postgres, and correct
        # for single- and multi-tag arrays alike. Multiple topics are OR-ed.
        q = q.where(or_(*[Article.topic_tags.cast(String).like(f'%"{t}"%') for t in topics]))
    if feedback is not None:
        q = q.where(Article.feedback == feedback)
    if min_signal is not None:
        q = q.where(Source.signal_score >= min_signal)

    # `total` is the post-ranking survivor count in ranked mode (set below), so
    # the COUNT query is only needed for the raw paginated (ranked=false) path.
    total = 0
    density = 0  # effective feed-density; set in the ranked path

    if ranked:
        from app.services.ranker import _get_source_affinity, _get_topic_weights
        from app.services.relevance import DEFAULT_PER_SOURCE_PER_DAY, explain

        window_days = TIME_RANGE_DAYS.get(time_range or "7d", 7)
        user_id = user.id if user else None
        density = await _feed_density(db, user)
        # Anti-domination cap (per source-category per day) is now decoupled from
        # the visible feed length: it just prevents one source crowding the pool
        # BEFORE we truncate the ranked result to `density`.
        per_day = DEFAULT_PER_SOURCE_PER_DAY

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

        # V7-6: the Feed is a finite ranked shortlist — truncate to feed-density so
        # it shows exactly N numbered items and never a "Show more". Discover passes
        # cap_to_density=false to page through the full ranked set instead.
        if cap_to_density:
            ordered_ids = ordered_ids[:density]
            total = len(ordered_ids)

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
        from app.services.hotness import heat_for

        heat_by_id = {a.id: heat_for(a, buzz.get(a.id, 1)) for a in items}
        for o in out_items:
            match, why = explanations.get(o.id, (None, None))
            o.relevance = match
            o.why = why or None
            score, level = heat_by_id.get(o.id, (None, 0))
            o.hotness = score
            o.heat = level

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
        density=density,
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
        apply_daily_caps, interleave_by_group, interleave_by_importance, score_map,
    )

    # Bound the candidate set to 2000. The ORDER BY that bound uses is critical:
    #   • Short horizons (≤7d) are freshness-led → newest 2000 (unchanged).
    #   • Long horizons (Month/Year) are importance-led catch-up. Drawing the
    #     newest 2000 is exactly why Month and Year rendered identically — with
    #     >2000 items in the last ~month, the "newest 2000" set is the SAME for a
    #     30d and a 365d filter, so the year never even sees older landmarks.
    #     Draw by traction instead so the year's landmark items are in the pool.
    if window_days > 7:
        candidate_order = (Article.trending_score.desc(), Article.published_at.desc())
    else:
        candidate_order = (Article.published_at.desc(),)
    all_result = await db.execute(q.order_by(*candidate_order).limit(2000))
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

    # Mix sources unless the query already narrowed to one source/category
    # (a single column is then the point). Day/Week stay freshness-led with
    # per-day buckets; Month/Year switch to importance-led catch-up ordering so
    # the horizons are genuinely different and aren't all blogs from today.
    if not source_id and not category:
        if window_days <= 7:
            ranked_items = interleave_by_group(
                ranked_items, window_days=window_days,
                category_of=category_of, scores=scores,
            )
        else:
            ranked_items = interleave_by_importance(
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
    """Ids the user has already opened — excluded from the dynamic feed.
    Opening is the only 'viewed' signal (no impression tracking)."""
    from app.models.user_article_state import UserArticleState

    result = await db.execute(
        select(UserArticleState.article_id).where(
            UserArticleState.user_id == user_id,
            UserArticleState.is_read.is_(True),
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


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    guest: bool = Depends(is_guest),
) -> ArticleOut:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Read-state is per-user (UserArticleState) for authed accounts, so one
    # person opening an article never marks it read for everyone else. Guests
    # are read-only; the legacy global column is used only for the anonymous,
    # single-user (AUTH_REQUIRED=false) deployment.
    from app.services.user_state import overlay_model

    if guest:
        return overlay_model(ArticleOut.model_validate(article), None)

    if user:
        from app.models.user_article_state import UserArticleState
        from app.services.user_state import upsert_state

        # First open is a weak implicit positive — learn the user's taste from what
        # they actually choose to read, not only explicit feedback (V7 Phase 2).
        existing = await db.get(UserArticleState, (user.id, article.id))
        first_open = existing is None or not existing.is_read
        state = await upsert_state(db, user.id, article.id, is_read=True)
        if first_open:
            from app.services.preference_learner import learn
            try:
                await learn(db, user, article, signal="view")
                await db.commit()
            except Exception:  # learning is best-effort; never block the read
                await db.rollback()
        return overlay_model(ArticleOut.model_validate(article), state)

    if not article.is_read:
        article.is_read = True
        await db.commit()
    return ArticleOut.model_validate(article)
