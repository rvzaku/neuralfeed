"""Cross-source duplicate suppression for the feed (V8, strengthened in V6).

The same story fetched via two sources (e.g. a paper from arxiv-cs-ai and
hf-papers) must surface exactly once: the most-engaged copy wins and absorbs
the other's topic tags.

V6 strengthens this beyond exact normalized-title matches: near-duplicate
headlines that survive different punctuation/word choice ("Meta releases Llama 4"
vs "Meta's Llama 4 is here") are clustered by token-set Jaccard overlap so the
feed reads as deduplicated, not noisy.
"""

import re

from app.models.article import Article

_NON_WORD = re.compile(r"[^\w\s]")
_STOP_WORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "is", "are",
    "was", "were", "with", "and", "or", "but", "by", "from", "as", "it",
    "its", "this", "that", "new", "now", "how", "why", "what",
}

# Two headlines whose significant-token sets overlap this much are treated as
# the same story. Tuned high enough to avoid collapsing distinct stories that
# merely share a subject (e.g. two different Llama articles).
_JACCARD_THRESHOLD = 0.7


def _tokens(title: str) -> frozenset:
    normalized = _NON_WORD.sub("", (title or "").lower())
    return frozenset(w for w in normalized.split() if w not in _STOP_WORDS and len(w) > 1)


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


def _cluster_keys(articles: list[Article]) -> dict:
    """Assign each article id a canonical cluster key.

    Articles sharing an exact normalized title_hash collapse immediately;
    remaining near-duplicate headlines are merged into the first cluster whose
    representative token set is sufficiently similar. The cluster key is the
    title_hash (or id) of the first article seen for that cluster — stable and
    independent of which copy ultimately wins.
    """
    cluster_of: dict = {}
    # Representative token set per cluster key, for fuzzy matching.
    reps: list[tuple[str, frozenset]] = []
    # Exact-hash fast path so identical stories never pay the O(n) scan.
    by_hash: dict = {}

    for a in articles:
        exact = a.title_hash or a.id
        if exact in by_hash:
            cluster_of[a.id] = by_hash[exact]
            continue

        toks = _tokens(a.title)
        match = None
        for key, rep_toks in reps:
            if _jaccard(toks, rep_toks) >= _JACCARD_THRESHOLD:
                match = key
                break

        if match is None:
            match = exact
            reps.append((exact, toks))
        by_hash[exact] = match
        cluster_of[a.id] = match

    return cluster_of


def cross_source_buzz(articles: list[Article]) -> dict:
    """Map article id -> number of *distinct sources* covering the same story.

    A story independently surfaced by arXiv, Reddit, and HF is gaining real
    traction; this 'mention count' is the cross-source buzz signal the feed
    uses to lift genuinely-discussed items above single-source noise (V6).
    """
    cluster_of = _cluster_keys(articles)
    sources_by_cluster: dict = {}
    for a in articles:
        sources_by_cluster.setdefault(cluster_of[a.id], set()).add(a.source_id)
    return {a.id: len(sources_by_cluster[cluster_of[a.id]]) for a in articles}


def dedupe_cross_source(articles: list[Article]) -> list[Article]:
    """Collapse each cluster to its most-engaged copy, merging topic tags."""
    cluster_of = _cluster_keys(articles)
    winners: dict = {}
    for a in articles:
        key = cluster_of[a.id]
        kept = winners.get(key)
        if kept is None:
            winners[key] = a
            continue
        winner, loser = (a, kept) if a.trending_score > kept.trending_score else (kept, a)
        merged = list(dict.fromkeys((winner.topic_tags or []) + (loser.topic_tags or [])))
        winner.topic_tags = merged
        winners[key] = winner
    return [a for a in articles if winners.get(cluster_of[a.id]) is a]
