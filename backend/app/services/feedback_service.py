"""Feedback application: persistence, source signal recompute, and adaptive
topic weights. The personalization loop lives here — the route stays thin.

Topic weights drive the smart ranker (services/ranker.py). Every thumbs
up/down nudges the weights of that article's topics so future ranking
reflects accumulated taste. Weights can also be set manually via
PUT /preferences/topic_weights, which uses the same storage key.
"""

import json
from typing import Optional

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.article import Article
from app.models.feedback_log import FeedbackLog
from app.models.source import Source
from app.models.user_preference import UserPreference

log = structlog.get_logger()

WEIGHT_STEP = 0.1
WEIGHT_FLOOR = -1.0
WEIGHT_CEILING = 2.0
UNWEIGHTED_TAGS = {"general"}  # catch-all carries no taste signal


class ArticleNotFound(Exception):
    pass


async def apply_feedback(article_id: str, value: int, db: AsyncSession) -> Article:
    """Set thumbs up/down (+1/-1, 0 clears), log it, recompute the source's
    signal score, and adapt topic weights. Returns the updated article."""
    article = await db.get(Article, article_id)
    if article is None:
        raise ArticleNotFound(article_id)

    article.feedback = value if value != 0 else None
    db.add(FeedbackLog(
        article_id=article_id,
        source_id=article.source_id,
        value=value,
        created_at=utcnow(),
    ))
    await db.commit()

    await _recompute_signal_score(article.source_id, db)
    if value in (1, -1):
        await _adjust_topic_weights(article.topic_tags or [], value, db)
    return article


async def _recompute_signal_score(source_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(
            func.count(Article.id).label("total"),
            func.sum(case((Article.feedback == 1, 1), else_=0)).label("positive"),
        ).where(Article.source_id == source_id, Article.feedback != None)  # noqa: E711
    )
    row = result.one()
    if row.total and row.total > 0:
        source = await db.get(Source, source_id)
        if source:
            source.signal_score = round((row.positive or 0) / row.total, 3)
            await db.commit()


async def _adjust_topic_weights(tags: list[str], direction: int, db: AsyncSession) -> None:
    pref: Optional[UserPreference] = await db.get(UserPreference, "topic_weights")
    try:
        weights: dict = json.loads(pref.value) if pref else {}
    except Exception:
        weights = {}

    delta = WEIGHT_STEP * direction
    for tag in tags:
        if tag in UNWEIGHTED_TAGS:
            continue
        weights[tag] = round(
            min(WEIGHT_CEILING, max(WEIGHT_FLOOR, weights.get(tag, 0.0) + delta)), 4
        )

    encoded = json.dumps(weights)
    if pref:
        pref.value = encoded
    else:
        db.add(UserPreference(key="topic_weights", value=encoded))
    await db.commit()
    log.info("topic_weights_adjusted", direction=direction, tags=tags)
