import json
import math
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.article import Article
from app.models.user_preference import UserPreference


async def _get_topic_weights(db: AsyncSession) -> dict:
    pref = await db.get(UserPreference, "topic_weights")
    if pref:
        try:
            return json.loads(pref.value)
        except Exception:
            pass
    return {}


async def _get_muted_sources(db: AsyncSession) -> set:
    pref = await db.get(UserPreference, "muted_sources")
    if pref:
        try:
            return set(json.loads(pref.value))
        except Exception:
            pass
    return set()


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
) -> float:
    if article.source_id in muted_sources:
        return -1.0

    recency = _recency_score(article.published_at)

    topic_boost = 0.0
    for tag in article.topic_tags:
        topic_boost += topic_weights.get(tag, 0.0)
    topic_boost = min(topic_boost, 1.0)

    trending = min(article.trending_score / 1000.0, 1.0) if article.trending_score > 0 else 0.0

    feedback_boost = 0.3 if article.feedback == 1 else (-0.5 if article.feedback == -1 else 0.0)

    score = (
        0.35 * recency
        + 0.30 * source_signal
        + 0.20 * topic_boost
        + 0.10 * trending
        + 0.05 * feedback_boost
    )
    return round(score, 4)


async def rank_articles(articles: list, db: AsyncSession) -> list:
    from app.models.source import Source
    topic_weights = await _get_topic_weights(db)
    muted_sources = await _get_muted_sources(db)

    source_ids = {a.source_id for a in articles}
    source_scores: dict = {}
    for sid in source_ids:
        src = await db.get(Source, sid)
        source_scores[sid] = src.signal_score if src else 0.5

    scored = [
        (a, score_article(a, source_scores.get(a.source_id, 0.5), topic_weights, muted_sources))
        for a in articles
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [a for a, _ in scored if _ >= 0]
