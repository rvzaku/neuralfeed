"""External traction for editorial articles (V10).

Blogs, newsletters, and company posts arrive with no native engagement metric —
unlike GitHub (stars) or Reddit (upvotes) there is no "how much is this gaining
traction" number on the item itself. But the wider community still reacts to
them: the same blog post gets submitted to Hacker News and Reddit, where it
accrues points, upvotes, and comments.

This service looks each editorial article's URL up on Hacker News (Algolia
search API) and Reddit (public `/api/info.json?url=`) and records the discussion
it found as the article's `engagement`, so the relevance ranker and the feed
card can treat a blog post that's blowing up on HN exactly like a trending repo.

Cost: zero LLM, two cheap unauthenticated HTTP calls per article, batched and
rate-limited by the scheduler. No content is stored — only public vote/comment
counts, which are metadata, not article text (CLAUDE.md data rule).
"""

import json
from datetime import timedelta
from typing import Optional

import httpx
import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.time import utcnow
from app.models.article import Article
from app.models.source import Source

log = structlog.get_logger()

# Categories whose items have no native engagement signal of their own.
EDITORIAL_CATEGORIES = ("company", "newsletter", "news", "podcast")
BATCH_SIZE = 30
TRACTION_TTL_HOURS = 24  # re-check a post's HN/Reddit traction at most daily
LOOKUP_TIMEOUT = 12.0


async def _hacker_news(client: httpx.AsyncClient, url: str) -> dict:
    """Best HN story for this exact URL: points + comments. Algolia indexes
    submissions by URL, so an exact-URL story (if any) is the canonical one."""
    try:
        resp = await client.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": url, "restrictSearchableAttributes": "url",
                    "tags": "story", "hitsPerPage": 5},
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
    except Exception as e:
        log.debug("hn_traction_lookup_failed", url=url, error=str(e))
        return {}

    best = {}
    for hit in hits:
        if (hit.get("url") or "").rstrip("/") != url.rstrip("/"):
            continue
        points = int(hit.get("points") or 0)
        if points >= best.get("points", -1):
            best = {
                "points": points,
                "comments": int(hit.get("num_comments") or 0),
                "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            }
    return best


async def _reddit(client: httpx.AsyncClient, url: str) -> dict:
    """Aggregate score + comments across every Reddit submission of this URL."""
    try:
        resp = await client.get(
            "https://www.reddit.com/api/info.json",
            params={"url": url},
            headers={"User-Agent": settings.reddit_user_agent},
        )
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])
    except Exception as e:
        log.debug("reddit_traction_lookup_failed", url=url, error=str(e))
        return {}

    score = comments = 0
    for child in children:
        data = child.get("data", {})
        score += int(data.get("score") or 0)
        comments += int(data.get("num_comments") or 0)
    if score <= 0 and comments <= 0:
        return {}
    return {"upvotes": score, "reddit_comments": comments}


async def fetch_external_engagement(url: str) -> dict:
    """Combined HN + Reddit traction for a URL. Empty dict when neither knows
    of it (the common case — most posts are never widely submitted)."""
    async with httpx.AsyncClient(timeout=LOOKUP_TIMEOUT, follow_redirects=True) as client:
        hn = await _hacker_news(client, url)
        rd = await _reddit(client, url)

    if not hn and not rd:
        return {}

    engagement: dict = {}
    engagement.update(hn)
    if rd:
        engagement["upvotes"] = rd["upvotes"]
        # Fold Reddit comments into the single comments figure for display
        engagement["comments"] = engagement.get("comments", 0) + rd["reddit_comments"]
    return engagement


def _traction_score(engagement: dict) -> float:
    """A single comparable popularity number from mixed signals: HN points
    weigh a bit more than raw Reddit upvotes (a smaller, higher-signal crowd)."""
    return float(engagement.get("points", 0)) * 1.5 + float(engagement.get("upvotes", 0))


async def enrich_editorial_traction(db: AsyncSession, limit: int = BATCH_SIZE) -> int:
    """Attach HN/Reddit traction to recent editorial articles that have none yet
    (or whose traction is stale). Returns the number updated with real signal."""
    cutoff = utcnow() - timedelta(days=7)
    stale_before = utcnow() - timedelta(hours=TRACTION_TTL_HOURS)

    editorial_ids = (await db.execute(
        select(Source.id).where(Source.category.in_(EDITORIAL_CATEGORIES))
    )).scalars().all()
    if not editorial_ids:
        return 0

    result = await db.execute(
        select(Article)
        .where(
            Article.source_id.in_(editorial_ids),
            Article.published_at >= cutoff,
            or_(Article.engagement_at.is_(None), Article.engagement_at < stale_before),
        )
        .order_by(Article.published_at.desc())
        .limit(limit)
    )
    articles = result.scalars().all()

    now = utcnow()
    updated = 0
    for article in articles:
        engagement = await fetch_external_engagement(article.url)
        # Stamp the check time regardless, so a post with no traction yet isn't
        # re-queried every run — it just gets revisited after the TTL.
        article.engagement_at = now
        if engagement:
            article.engagement = json.dumps(engagement)
            score = _traction_score(engagement)
            if score > article.trending_score:
                article.trending_score = score
            updated += 1
        await db.commit()

    if articles:
        log.info("editorial_traction_complete", checked=len(articles), with_traction=updated)
    return updated
