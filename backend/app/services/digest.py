"""Daily "Today in AI" digest — the top handful of stories rolled up.

Reuses the same ranker the feed uses (so the digest reflects freshness +
relevance + traction + the user's learned taste), then trims to a short,
shareable set. Used by both the in-app digest endpoint and the scheduled email.
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.article import Article
from app.models.source import Source

DEFAULT_LIMIT = 5
# Prefer the last day; if it's quiet, widen so the digest is never empty.
_WINDOWS_HOURS = (24, 72, 24 * 7)


def _blurb(article: Article) -> Optional[str]:
    """One-line context for the story: the cached LLM 'why this matters' line if
    we have it, otherwise a trimmed snippet of the summary."""
    if article.context_line:
        return article.context_line.strip()
    if article.summary:
        s = article.summary.strip().replace("\n", " ")
        return (s[:197] + "…") if len(s) > 198 else s
    return None


async def build_digest(
    db: AsyncSession,
    user_id: Optional[str] = None,
    *,
    limit: int = DEFAULT_LIMIT,
) -> dict:
    """Return the ranked top-N recent stories as a JSON-ready dict."""
    from app.services.ranker import rank_articles

    items: list[Article] = []
    used_hours = _WINDOWS_HOURS[-1]
    for hours in _WINDOWS_HOURS:
        cutoff = utcnow() - timedelta(hours=hours)
        result = await db.execute(
            select(Article)
            .where(Article.published_at >= cutoff)
            .order_by(Article.published_at.desc())
            .limit(500)
        )
        items = list(result.scalars().all())
        used_hours = hours
        if len(items) >= limit:
            break

    ranked, _ = await rank_articles(items, db, user_id=user_id, window_days=1)
    top = ranked[:limit]

    names: dict[str, str] = {}
    if top:
        src_rows = await db.execute(
            select(Source.id, Source.name).where(
                Source.id.in_({a.source_id for a in top})
            )
        )
        names = {sid: name for sid, name in src_rows.all()}

    return {
        "generated_at": utcnow().isoformat(),
        "window_hours": used_hours,
        "count": len(top),
        "items": [
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "source_id": a.source_id,
                "source_name": names.get(a.source_id, a.source_id),
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "topic_tags": a.topic_tags or [],
                "blurb": _blurb(a),
            }
            for a in top
        ],
    }
