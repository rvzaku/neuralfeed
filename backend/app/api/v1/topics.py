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
from app.services.dedupe import cross_source_buzz
from app.services.hotness import topic_heat
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

    # Load recent articles in full (not just tag arrays) so the Hotness Index can
    # score cross-source velocity per topic. Bounded to the freshest 2000 to keep
    # the scan cheap.
    rows = await db.execute(
        select(Article)
        .where(Article.published_at >= cutoff)
        .order_by(Article.published_at.desc())
        .limit(2000)
    )
    articles = list(rows.scalars().all())

    counts: Counter = Counter()
    for a in articles:
        for tag in a.topic_tags or []:
            counts[tag] += 1

    # Per-topic heat from cross-source velocity (V6 Hotness Index).
    buzz = cross_source_buzz(articles)
    heat = topic_heat(articles, buzz)

    weights = await _get_topic_weights(db, user.id if user else None)

    items = [
        {
            "tag": tag,
            "count": counts.get(tag, 0),
            "weight": round(float(weights.get(tag, 0.0)), 3),
            "heat": heat.get(tag, 0),
        }
        for tag in TOPIC_KEYWORDS
    ]

    # Relevance order: topics with fresh material first, then what's hot right
    # now (cross-source velocity), then the ones the user leans into (learned
    # weight), then raw volume as the tiebreaker.
    items.sort(
        key=lambda i: (i["count"] > 0, i["heat"], i["weight"], i["count"]),
        reverse=True,
    )

    return {"items": items, "time_range": time_range}
