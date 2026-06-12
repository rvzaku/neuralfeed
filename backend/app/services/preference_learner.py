"""Implicit personalization from likes/dislikes/bookmarks (V8, app-feedback-v5).

Replaces the manual topic-weight sliders: every feedback event nudges the
user's topic weights and per-source affinity, so 'NeuralFeed should know by
likes, dislikes and saves which feed to suggest'. Pure incremental updates —
no LLM, no batch job, fully inspectable in the preferences table.
"""

import json
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.user_preference import UserPreference

log = structlog.get_logger()

# Deltas per signal; dislikes push harder than likes so noise gets buried fast
_DELTAS = {"like": 0.15, "dislike": -0.25, "bookmark": 0.30, "unlike": -0.15, "undislike": 0.25}
_CLAMP = 1.0


def _key(user, name: str) -> str:
    return f"u:{user.id}:{name}" if user else name


async def _load(db: AsyncSession, key: str) -> dict:
    pref = await db.get(UserPreference, key)
    if pref:
        try:
            data = json.loads(pref.value)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


async def _store(db: AsyncSession, key: str, data: dict) -> None:
    pref = await db.get(UserPreference, key)
    value = json.dumps(data)
    if pref:
        pref.value = value
    else:
        db.add(UserPreference(key=key, value=value))


def _nudge(weights: dict, keys: list, delta: float) -> dict:
    for k in keys:
        weights[k] = round(max(-_CLAMP, min(_CLAMP, float(weights.get(k, 0.0)) + delta)), 3)
        if weights[k] == 0.0:
            weights.pop(k)
    return weights


async def learn(
    db: AsyncSession,
    user,
    article: Article,
    signal: str,
    previous_feedback: Optional[int] = None,
) -> None:
    """Update topic weights + source affinity for one feedback event.
    `signal`: like | dislike | bookmark. Toggling a reaction off reverses it.
    Commits as part of the caller's transaction (no own commit)."""
    if signal == "like" and previous_feedback == 1:
        signal = "unlike"
    elif signal == "dislike" and previous_feedback == -1:
        signal = "undislike"
    delta = _DELTAS.get(signal)
    if delta is None:
        return

    topics_key = _key(user, "topic_weights")
    affinity_key = _key(user, "source_affinity")

    topics = await _load(db, topics_key)
    await _store(db, topics_key, _nudge(topics, article.topic_tags or [], delta))

    affinity = await _load(db, affinity_key)
    await _store(db, affinity_key, _nudge(affinity, [article.source_id], delta))

    log.info("preference_learned", signal=signal, source_id=article.source_id,
             tags=article.topic_tags, user=bool(user))
