"""Topic directory with relevance ordering.

The feed already tags every article with topic slugs and the preference_learner
keeps a per-user `topic_weights` map (nudged by likes/saves/dislikes). This
endpoint joins the two so the Topics page can lead with what the user actually
finds useful — topics they engage with, then topics with the most fresh
material — and push empty/quiet topics out of the way instead of showing dead
cards.
"""

from collections import Counter
from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.time import utcnow
from app.models.article import Article
from app.services.ranker import _get_topic_weights
from app.services.topic_tagger import TOPIC_KEYWORDS

router = APIRouter(prefix="/topics", tags=["topics"])

TIME_RANGE_DAYS = {"1d": 1, "3d": 3, "7d": 7, "30d": 30}


@router.get("")
async def list_topics(
    time_range: str = Query("7d", pattern="^(1d|3d|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    cutoff = utcnow() - timedelta(days=TIME_RANGE_DAYS[time_range])

    # One scan of recent tag arrays → per-topic fresh counts. Counting in Python
    # keeps it portable (generic JSON column, no per-dialect array operators).
    rows = await db.execute(
        select(Article.topic_tags).where(Article.published_at >= cutoff)
    )
    counts: Counter = Counter()
    for (tags,) in rows.all():
        for tag in tags or []:
            counts[tag] += 1

    weights = await _get_topic_weights(db, user.id if user else None)

    items = [
        {
            "tag": tag,
            "count": counts.get(tag, 0),
            "weight": round(float(weights.get(tag, 0.0)), 3),
        }
        for tag in TOPIC_KEYWORDS
    ]

    # Relevance order: topics with fresh material first, then the ones the user
    # leans into (learned weight), then raw volume as the tiebreaker.
    items.sort(key=lambda i: (i["count"] > 0, i["weight"], i["count"]), reverse=True)

    return {"items": items, "time_range": time_range}
