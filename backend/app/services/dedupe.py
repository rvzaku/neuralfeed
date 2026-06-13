"""Cross-source duplicate suppression for the feed (V8).

The same story fetched via two sources (e.g. a paper from arxiv-cs-ai and
hf-papers) must surface exactly once: the most-engaged copy wins and absorbs
the other's topic tags.
"""

from app.models.article import Article


def cross_source_buzz(articles: list[Article]) -> dict:
    """Map article id -> number of *distinct sources* covering the same story.

    A story independently surfaced by arXiv, Reddit, and HF is gaining real
    traction; this 'mention count' is the cross-source buzz signal the feed
    uses to lift genuinely-discussed items above single-source noise (V6).
    """
    sources_by_story: dict = {}
    for a in articles:
        key = a.title_hash or a.id
        sources_by_story.setdefault(key, set()).add(a.source_id)
    return {
        a.id: len(sources_by_story.get(a.title_hash or a.id, {a.source_id}))
        for a in articles
    }


def dedupe_cross_source(articles: list[Article]) -> list[Article]:
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
