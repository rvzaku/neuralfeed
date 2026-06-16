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

# Open aggregators publish whatever is trending on their platform, AI or not, so a
# "general"-only (unclassified) item from one is almost always off-topic noise — a
# viral non-AI GitHub repo ("Watch free TV"), HN post, or subreddit thread that was
# crowding out real AI signal (app-feedback-v7). Curated/AI-native sources (arXiv,
# HF, company blogs, newsletters, podcasts) are about AI by construction, so an
# untagged item there is just a tagger miss, not noise — it gets only a light touch.
_BROAD_AGGREGATOR_PREFIXES = (
    "github", "hackernews", "reddit", "producthunt", "twitter", "nitter",
    "youtube", "linkedin",
)


def _is_broad_aggregator(source_id: str) -> bool:
    return source_id.startswith(_BROAD_AGGREGATOR_PREFIXES)


def score_article(
    article: Article,
    source_signal: float,
    topic_weights: dict,
    muted_sources: set,
    source_affinity: float = 0.0,
    window_days: int = 7,
    landmark_matcher=None,
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

    # Topicality (relevance precision, app-feedback-v7): an item the tagger could
    # only file under the catch-all "general" tag is unclassified. The penalty is
    # PROPORTIONAL to the item's own relevance (so a high-traction junk repo sinks
    # a lot, not a flat nudge) and SOURCE-AWARE: hard for open aggregators where
    # "general" means non-AI noise, light for AI-native sources where it's just a
    # tagger miss. Specifically-tagged items are untouched.
    tags = article.topic_tags or []
    specific = [t for t in tags if t != "general"]
    if specific:
        topicality = 0.0
    else:
        rate = 0.60 if _is_broad_aggregator(article.source_id) else 0.15
        topicality = -rate * base

    # Landmark boost (app-feedback-v6): an item naming a current breakout launch
    # (OpenClaw, Moltbook — detected by scripts/detect_landmarks.py) is "what the
    # whole field is talking about", so it earns a real lift even when it carries
    # no per-item upvote/star traction. Bounded so it informs, never dominates.
    from app.services.landmarks import title_is_landmark
    landmark_boost = 0.20 if title_is_landmark(article.title, landmark_matcher) else 0.0

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
        + landmark_boost
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
    landmark_matcher=None,
) -> "tuple[list, dict]":
    """Rank a candidate set. Returns (kept_articles, final_score_by_id).

    The score map is the authoritative ranking signal — it carries the
    topicality penalty and the learned topic/source/feedback personalization on
    top of base relevance. The caller MUST feed this map (not the raw
    relevance_score) into the interleave step, or that downstream re-sort would
    silently discard every refinement computed here.

    The caller (feed endpoint) already needs the user's topic_weights/
    source_affinity to render the "why" line, so it passes them in to avoid
    re-querying the preferences table three times per request."""
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
            window_days=window_days, landmark_matcher=landmark_matcher,
        ))
        for a in articles
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    # Drop muted (-1) and sub-threshold noise — but never return an empty feed:
    # if everything is low-relevance, keep the top items so the page isn't blank.
    kept = [a for a, s in scored if s >= MIN_RELEVANCE]
    if not kept:
        kept = [a for a, s in scored if s >= 0][:20]
    final_scores = {a.id: s for a, s in scored}
    return kept, final_scores
