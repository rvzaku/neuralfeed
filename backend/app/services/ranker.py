import json
import math
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.article import Article
from app.models.user_preference import UserPreference


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


def score_article(
    article: Article,
    source_signal: float,
    topic_weights: dict,
    muted_sources: set,
    source_affinity: float = 0.0,
) -> float:
    if article.source_id in muted_sources:
        return -1.0

    recency = _recency_score(article.published_at)

    # Learned from likes/dislikes/saves (V8) — can be negative
    topic_boost = 0.0
    for tag in article.topic_tags:
        topic_boost += topic_weights.get(tag, 0.0)
    topic_boost = max(-1.0, min(topic_boost, 1.0))

    trending = min(article.trending_score / 1000.0, 1.0) if article.trending_score > 0 else 0.0

    feedback_boost = 0.3 if article.feedback == 1 else (-0.5 if article.feedback == -1 else 0.0)

    score = (
        0.35 * recency
        + 0.30 * source_signal
        + 0.20 * topic_boost
        + 0.10 * trending
        + 0.05 * feedback_boost
        # Learned source affinity rides on top (±0.1) instead of diluting the
        # base weights — users without feedback history rank exactly as before
        + 0.10 * source_affinity
    )
    return round(score, 4)


async def rank_articles(articles: list, db: AsyncSession, user_id=None) -> list:
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
        ))
        for a in articles
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [a for a, _ in scored if _ >= 0]
