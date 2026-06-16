"""Re-tag every article's topic_tags with the current tagger.

Run after changing topic_tagger.py so the existing corpus reflects the new
(more precise) classification, not just newly-ingested items:

    DATABASE_URL=... python -m scripts.retag

Idempotent and safe: it only rewrites the topic_tags column, in batches, and
only when the computed tags actually differ.
"""

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.article import Article
from app.services.topic_tagger import tag_topics


async def retag() -> None:
    changed = scanned = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Article))
        articles = result.scalars().all()
        for a in articles:
            scanned += 1
            tags = tag_topics(f"{a.title} {a.summary or ''}")
            if tags != (a.topic_tags or []):
                a.topic_tags = tags
                changed += 1
        await db.commit()
    print(f"retag complete: {changed} updated / {scanned} scanned")


if __name__ == "__main__":
    asyncio.run(retag())
