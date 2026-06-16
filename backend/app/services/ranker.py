import json
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

    # Topicality (relevance precision, app-feedback-v7): the keyword tagger files
    # items it can't classify into a specific AI topic under the catch-all
    # "general" tag. A high-traction item that is only "general" is the classic
    # off-topic noise (a viral non-AI Hacker News post) that made the feed feel
    # irrelevant — penalize it so genuine AI stories outrank it. Specifically
    # tagged items are unaffected.
    tags = article.topic_tags or []
    specific = [t for t in tags if t != "general"]
    topicality = -0.18 if not specific else 0.0

    # V6: lean harder on what the user actually likes. Learned topic affinity and
    # source affinity now carry more weight so off-preference items visibly sink
    # (and disliked topics, which contribute negative topic_boost, sink hardest)
    # without ever overpowering base recency×traction.
    score = (
        base
        + 0.25 * topic_boost
        + 0.15 * source_affinity
        + 0.10 * (source_signal - 0.5)   # quality nudge, centered so 0.5 is neutral
        + 0.10 * feedback_boost
        + topicality
    )
    return round(score, 4)


async def rank_articles(
    articles: list,
    db: AsyncSession,
    user_id=None,
    window_days: int = 7,
    topic_weights: Optional[dict] = None,
    source_affinity: Optional[dict] = None,
    muted_sources: Optional[set] = None,
) -> list:
    """Rank a candidate set. The caller (feed endpoint) already needs the user's
    topic_weights/source_affinity to render the "why" line, so it passes them in
    to avoid re-querying the preferences table three times per request."""
    from app.models.source import Source
    if topic_weights is None:
        topic_weights = await _get_topic_weights(db, user_id)
    if source_affinity is None:
        source_affinity = await _get_source_affinity(db, user_id)
    if muted_sources is None:
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
