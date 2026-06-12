"""Group related articles into event 'stories' so the feed feels finite.

A story is e.g. "Qwen 3 released": one card that bundles the arXiv paper,
GitHub repo, Reddit threads, and blog posts about the same event, instead
of a dozen near-duplicate feed items. Clustering is lexical (no LLM):
articles whose title signatures overlap beyond a threshold are merged.

Computed on demand over a recent window; no extra tables. Single-user
scale today; the pure functions here can move behind a worker later.
"""

import hashlib
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.source import Source

# Words too generic to signal a shared event in AI-news titles
_STOP = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "is", "are", "was",
    "were", "with", "and", "or", "but", "by", "from", "as", "it", "its", "this",
    "that", "be", "has", "have", "had", "will", "can", "could", "should", "would",
    "new", "using", "use", "how", "what", "why", "when", "you", "your", "we",
    "our", "i", "my", "me", "they", "their", "his", "her", "vs", "via", "into",
    "ai", "ml", "model", "models", "paper", "papers", "code", "release",
    "released", "releases", "announcing", "introducing", "show", "shows",
    "discussion", "question", "help", "best", "top", "now", "just", "out",
}
_NON_WORD = re.compile(r"[^\w\s]")
_SIM_THRESHOLD = 0.4  # conservative: prefer singleton stories over wrong merges
_MIN_SHARED = 2       # require at least 2 shared signature tokens


def title_signature(title: str) -> frozenset:
    normalized = _NON_WORD.sub(" ", title.lower())
    # Keep single-digit tokens — version numbers ("Qwen 3") are strong signals
    return frozenset(
        w for w in normalized.split()
        if w not in _STOP and (len(w) > 1 or w.isdigit())
    )


def _similarity(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    shared = a & b
    if len(shared) < _MIN_SHARED:
        return 0.0
    return len(shared) / min(len(a), len(b))


def dedupe_cross_source(articles: list[Article]) -> list[Article]:
    """Drop exact same-title duplicates that arrived via different sources
    (e.g. the same paper from arxiv-cs-ai and hf-papers). The most-engaged
    copy survives and absorbs the others' topic tags — one item, many tags,
    never repeated (app-feedback-v4)."""
    by_hash: dict = {}
    for a in articles:
        key = a.title_hash or a.id
        kept = by_hash.get(key)
        if kept is None:
            by_hash[key] = a
        else:
            winner, loser = (a, kept) if a.trending_score > kept.trending_score else (kept, a)
            merged = list(dict.fromkeys((winner.topic_tags or []) + (loser.topic_tags or [])))
            winner.topic_tags = merged
            by_hash[key] = winner
    return [a for a in articles if by_hash.get(a.title_hash or a.id) is a]


def cluster_articles(
    articles: list[Article], read_ids: Optional[set] = None, window_days: int = 7
) -> list[dict]:
    """Greedy single-pass clustering on title signatures.
    Returns story dicts sorted by total relevance descending."""
    from app.services.relevance import relevance_score

    articles = dedupe_cross_source(articles)
    clusters: list[dict] = []
    for article in articles:
        sig = title_signature(article.title)
        best, best_score = None, 0.0
        for cluster in clusters:
            score = _similarity(sig, cluster["signature"])
            if score > best_score:
                best, best_score = cluster, score
        if best is not None and best_score >= _SIM_THRESHOLD:
            best["articles"].append(article)
            # Tighten the centroid to the shared core so chains don't drift
            shared = best["signature"] & sig
            if len(shared) >= _MIN_SHARED:
                best["signature"] = shared
        else:
            clusters.append({"signature": sig, "articles": [article]})

    stories = []
    for cluster in clusters:
        arts = cluster["articles"]
        story_id = hashlib.sha256(
            " ".join(sorted(cluster["signature"]) or [arts[0].id]).encode()
        ).hexdigest()[:12]
        # Headline: most-engaged item wins; ties go to the newest
        lead = max(arts, key=lambda a: (a.trending_score, a.published_at))
        tag_counts = Counter(t for a in arts for t in (a.topic_tags or []))
        # Multi-source corroboration multiplies relevance — an event echoed
        # across platforms matters more than one popular post
        story_relevance = sum(relevance_score(a, window_days) for a in arts)
        stories.append({
            "id": story_id,
            "headline": lead.title,
            "lead_article_id": lead.id,
            "image_url": lead.image_url,
            "article_count": len(arts),
            "source_count": len({a.source_id for a in arts}),
            "source_ids": list(dict.fromkeys(a.source_id for a in arts)),
            "topic_tags": [t for t, _ in tag_counts.most_common(4)],
            "latest_at": max(a.published_at for a in arts).isoformat(),
            "total_trending": sum(a.trending_score for a in arts),
            "relevance": round(story_relevance, 4),
            "summary": lead.summary,
            "context_line": lead.context_line,
            "is_read": all((a.id in read_ids) if read_ids is not None else a.is_read for a in arts),
            "article_ids": [a.id for a in arts],
        })

    stories.sort(key=lambda s: s["relevance"], reverse=True)
    return stories


async def get_stories(
    db: AsyncSession,
    days: int = 1,
    limit: int = 12,
    unread_only: bool = True,
    topic: Optional[str] = None,
    read_ids: Optional[set] = None,  # per-user read overlay (None = global columns)
) -> dict:
    """Bounded story digest: at most `limit` stories — the feed must end."""
    from app.services.relevance import apply_daily_caps

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    q = (
        select(Article)
        .where(Article.published_at >= cutoff)
        .order_by(Article.published_at.desc())
        .limit(2000)
    )
    result = await db.execute(q)
    articles = list(result.scalars().all())
    if unread_only:
        if read_ids is not None:
            articles = [a for a in articles if a.id not in read_ids]
        else:
            articles = [a for a in articles if not a.is_read]
    if topic:
        articles = [a for a in articles if topic in (a.topic_tags or [])]

    # Relevance gate before clustering: only items that earned attention on
    # their platform compete for the front page (V7 anti-overwhelm)
    cat_result = await db.execute(select(Source.id, Source.category))
    category_of = {sid: cat for sid, cat in cat_result.all()}
    articles = apply_daily_caps(articles, window_days=days, category_of=category_of)

    stories = cluster_articles(articles, read_ids=read_ids, window_days=days)
    return {
        "stories": stories[:limit],
        "total_stories": len(stories),
        "window_days": days,
        "caught_up": len(stories) <= limit,
    }


async def get_story_detail(
    db: AsyncSession, article_ids: list[str], states: Optional[dict] = None
) -> dict:
    """Everything related to one story, grouped by source category."""
    if not article_ids:
        return {"groups": {}}
    result = await db.execute(select(Article).where(Article.id.in_(article_ids)))
    articles = result.scalars().all()
    source_ids = {a.source_id for a in articles}
    src_result = await db.execute(select(Source).where(Source.id.in_(source_ids)))
    categories = {s.id: s.category for s in src_result.scalars().all()}

    groups: dict[str, list] = {}
    for a in sorted(articles, key=lambda x: x.trending_score, reverse=True):
        groups.setdefault(categories.get(a.source_id, "other"), []).append({
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "source_id": a.source_id,
            "author": a.author,
            "summary": a.summary,
            "published_at": a.published_at.isoformat(),
            "trending_score": a.trending_score,
            "is_read": states[a.id].is_read if states and a.id in states else (a.is_read if states is None else False),
            "is_bookmarked": states[a.id].is_bookmarked if states and a.id in states else (a.is_bookmarked if states is None else False),
            "feedback": states[a.id].feedback if states and a.id in states else (a.feedback if states is None else None),
            "topic_tags": a.topic_tags or [],
            "image_url": a.image_url,
        })
    return {"groups": groups}
