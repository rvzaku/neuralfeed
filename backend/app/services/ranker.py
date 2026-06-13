import json
import math
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.article import Article
from app.models.user_preference import UserPreference
from app.services.relevance import relevance_score


async def _get_pref(db: AsyncSession, name: str, user_id=None):
    """User-namespaced preference with global fallback."""
    for key in ([f"u:{user_id}:{name}"] if user_id else []) + [name]:
        pref = await db.get(UserPreference, key)
        if pref:
            try:
                return json.loads(pref.value)
            except Exception:
                continue
    return None


async def _get_topic_weights(db: AsyncSession, user_id=None) -> dict:
    return await _get_pref(db, "topic_weights", user_id) or {}


async def _get_source_affinity(db: AsyncSession, user_id=None) -> dict:
    return await _get_pref(db, "source_affinity", user_id) or {}


async def _get_muted_sources(db: AsyncSession, user_id=None) -> set:
    return set(await _get_pref(db, "muted_sources", user_id) or [])


def _recency_score(published_at: datetime, half_life_days: float = 3.0) -> float:
    now = datetime.now(timezone.utc)
    pub = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    age_days = max(0, (now - pub).total_seconds() / 86400)
    return math.exp(-age_days * math.log(2) / half_life_days)


# Below this base relevance an item is stale/untracted noise — dropped from the
# ranked feed entirely (it stays reachable via ranked=false). Keeps the promise
# that the feed only shows what actually gained traction (feedback-feed-philosophy).
MIN_RELEVANCE = 0.04


def score_article(
    article: Article,
    source_signal: float,
    topic_weights: dict,
    muted_sources: set,
    source_affinity: float = 0.0,
    window_days: int = 7,
) -> float:
    """Final feed score. The DOMINANT term is the same recency×popularity
    relevance the card's "% match" shows — so the ordering can never contradict
    the label. Personalization (learned topic/source affinity, explicit
    feedback) and source quality ride ON TOP as bounded deltas, not as
    competing base weights."""
    if article.source_id in muted_sources:
        return -1.0

    # Base relevance: identical formula to relevance.explain()'s match, so sort
    # order tracks the displayed percentage.
    base = relevance_score(article, window_days)  # 0..1

    # Learned from likes/dislikes/saves (V8) — can be negative
    topic_boost = 0.0
    for tag in article.topic_tags:
        topic_boost += topic_weights.get(tag, 0.0)
    topic_boost = max(-1.0, min(topic_boost, 1.0))

    feedback_boost = 0.3 if article.feedback == 1 else (-0.5 if article.feedback == -1 else 0.0)

    score = (
        base
        + 0.15 * topic_boost
        + 0.10 * source_affinity
        + 0.10 * (source_signal - 0.5)   # quality nudge, centered so 0.5 is neutral
        + 0.10 * feedback_boost
    )
    return round(score, 4)


async def rank_articles(articles: list, db: AsyncSession, user_id=None, window_days: int = 7) -> list:
    from app.models.source import Source
    topic_weights = await _get_topic_weights(db, user_id)
    source_affinity = await _get_source_affinity(db, user_id)
    muted_sources = await _get_muted_sources(db, user_id)

    source_ids = {a.source_id for a in articles}
    source_scores: dict = {}
    if source_ids:
        result = await db.execute(
            select(Source.id, Source.signal_score).where(Source.id.in_(source_ids))
        )
        source_scores = {sid: score for sid, score in result.all()}

    scored = [
        (a, score_article(
            a, source_scores.get(a.source_id, 0.5), topic_weights, muted_sources,
            source_affinity=float(source_affinity.get(a.source_id, 0.0)),
            window_days=window_days,
        ))
        for a in articles
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    # Drop muted (-1) and sub-threshold noise — but never return an empty feed:
    # if everything is low-relevance, keep the top items so the page isn't blank.
    kept = [a for a, s in scored if s >= MIN_RELEVANCE]
    if not kept:
        kept = [a for a, s in scored if s >= 0][:20]
    return kept
