"""Detect current landmark launches from recent titles and store them.

One batched LLM pass over the freshest titles → the canonical landmark entity
names (OpenClaw, Moltbook, …), saved as a global preference the ranker boosts and
the curator preserves. Cheap enough to run on a schedule (e.g. daily).

    GROQ_API_KEY=... python -m scripts.detect_landmarks
"""

import asyncio
from datetime import timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.time import utcnow
from app.models.article import Article
from app.services.landmarks import (
    detect_landmark_entities,
    filter_distinctive,
    store_landmark_entities,
)

# Landmarks are a "right now" signal — look at the last few weeks of titles.
WINDOW_DAYS = 21


async def main() -> None:
    async with AsyncSessionLocal() as db:
        cutoff = utcnow() - timedelta(days=WINDOW_DAYS)
        rows = await db.execute(
            select(Article.title)
            .where(Article.published_at >= cutoff)
            .order_by(Article.published_at.desc())
        )
        titles = [t for (t,) in rows.all() if t]
        print(f"scanning {len(titles)} titles from the last {WINDOW_DAYS}d…")
        raw = await detect_landmark_entities(titles)
        entities = filter_distinctive(raw, titles)
        dropped = sorted(set(raw) - set(entities))
        await store_landmark_entities(db, entities)
        print(f"stored {len(entities)} distinctive landmarks: {entities}")
        if dropped:
            print(f"dropped {len(dropped)} too-common: {dropped}")


if __name__ == "__main__":
    asyncio.run(main())
