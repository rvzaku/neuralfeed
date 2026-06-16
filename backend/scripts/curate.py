"""Curate the corpus into a matured, relevant set (see docs/PLAN_CORPUS_CURATION.md).

Retention tightens with age: fresh items kept broadly, older items only if they
were genuinely important, ancient items dropped — but anything the user engaged
with (any row in user_article_state) is always preserved.

    python -m scripts.curate              # DRY RUN: report only, deletes nothing
    CURATE_APPLY=1 python -m scripts.curate   # actually delete the dropped set

Idempotent and safe: deletions never touch a preserved (user-referenced)
article, so there is no dangling foreign key.
"""

import asyncio
import os

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.core.time import utcnow
from app.models.article import Article
from app.models.user_article_state import UserArticleState
from app.services.ranker import _is_broad_aggregator
from app.services.relevance import importance_magnitude, popularity

# Tier boundaries (days) and thresholds — see the plan doc; tune here.
FRESH_DAYS, RECENT_DAYS, OLD_DAYS = 14, 90, 365
FRESH_JUNK_MAG = 0.25       # broad-aggregator general-only below this = junk
RECENT_MIN_MAG, RECENT_MIN_POP = 0.15, 0.50
OLD_LANDMARK_MAG = 0.45


def _age_days(article: Article, now) -> float:
    from datetime import timezone
    pub = article.published_at
    pub = pub.replace(tzinfo=timezone.utc) if pub.tzinfo is None else pub.astimezone(timezone.utc)
    now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return (now - pub).total_seconds() / 86400


def _keep(article: Article, now) -> "tuple[bool, str]":
    """(keep?, tier) for a non-preserved article."""
    age = _age_days(article, now)
    tags = article.topic_tags or []
    specific = any(t != "general" for t in tags)
    ai_relevant = specific or not _is_broad_aggregator(article.source_id)
    mag = importance_magnitude(article)

    if age <= FRESH_DAYS:
        junk = _is_broad_aggregator(article.source_id) and not specific and mag < FRESH_JUNK_MAG
        return (not junk, "fresh")
    if age <= RECENT_DAYS:
        return (ai_relevant and (mag >= RECENT_MIN_MAG or popularity(article) >= RECENT_MIN_POP), "recent")
    if age <= OLD_DAYS:
        return (specific and mag >= OLD_LANDMARK_MAG, "older")
    return (False, "ancient")


async def curate() -> None:
    apply = os.environ.get("CURATE_APPLY") == "1"
    now = utcnow()
    async with AsyncSessionLocal() as db:
        preserved = {
            row[0] for row in (await db.execute(select(UserArticleState.article_id))).all()
        }
        articles = (await db.execute(select(Article))).scalars().all()

        drop_ids: list[str] = []
        tiers: dict[str, list[int]] = {}  # tier -> [kept, dropped]
        for a in articles:
            if a.id in preserved:
                tiers.setdefault("preserved", [0, 0])[0] += 1
                continue
            keep, tier = _keep(a, now)
            t = tiers.setdefault(tier, [0, 0])
            if keep:
                t[0] += 1
            else:
                t[1] += 1
                drop_ids.append(a.id)

        total = len(articles)
        print(f"corpus: {total} articles, {len(preserved)} preserved (user-engaged)")
        for tier in ("preserved", "fresh", "recent", "older", "ancient"):
            if tier in tiers:
                kept, dropped = tiers[tier]
                print(f"  {tier:10} keep={kept:>5}  drop={dropped:>5}")
        print(f"=> would drop {len(drop_ids)} / {total}  ({100*len(drop_ids)/total:.0f}%)")

        if not apply:
            print("DRY RUN — nothing deleted. Re-run with CURATE_APPLY=1 to apply.")
            return

        for i in range(0, len(drop_ids), 500):
            batch = drop_ids[i:i + 500]
            await db.execute(delete(Article).where(Article.id.in_(batch)))
        await db.commit()
        print(f"deleted {len(drop_ids)} articles; corpus now {total - len(drop_ids)}")


if __name__ == "__main__":
    asyncio.run(curate())
