"""Cross-source duplicate suppression for the feed (V8).

The same story fetched via two sources (e.g. a paper from arxiv-cs-ai and
hf-papers) must surface exactly once: the most-engaged copy wins and absorbs
the other's topic tags.
"""

from app.models.article import Article


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
