"""V7 relevance engine: recency × popularity scoring, per-day top-N caps,
and category interleaving.

The anti-overwhelm contract (app-feedback-v4): with a month of data in the
DB, the user must still only see the handful of items per source per day
that actually gained traction — never the raw firehose.

Popularity is normalized per source family (500 Reddit upvotes ≠ 500 GitHub
stars) with log scaling, so cross-source comparison is meaningful. Editorial
sources without engagement metrics (blogs, newsletters) get a neutral
baseline — their selectivity is the publication itself.
"""

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from app.models.article import Article

DEFAULT_PER_SOURCE_PER_DAY = 10

# log10 of the engagement value that counts as "fully popular" per family
_SATURATION = {
    "reddit": 3.0,    # ~1k upvotes
    "hackernews": 2.7,  # ~500 points
    "github": 4.0,    # ~10k stars (or 2.5 ≈ 300 stars today, see below)
    "hf": 2.0,        # ~100 HF upvotes
    "arxiv": 2.0,     # traction-boosted upvotes via HF Daily Papers
}
_EDITORIAL_BASELINE = 0.45  # blogs/newsletters/podcasts: curated, no votes


def _source_family(source_id: str) -> str:
    for family in ("reddit", "hackernews", "github", "arxiv"):
        if source_id.startswith(family):
            return family
    if source_id.startswith("hf-"):
        return "hf"
    return "editorial"


def _log_norm(value: float, saturation_log10: float) -> float:
    if value <= 0:
        return 0.0
    return min(math.log10(value + 1) / saturation_log10, 1.0)


def popularity(article: Article) -> float:
    """0..1 popularity normalized per source family."""
    family = _source_family(article.source_id)
    if family == "editorial":
        return _EDITORIAL_BASELINE

    engagement: dict = {}
    if article.engagement:
        try:
            engagement = json.loads(article.engagement)
        except (json.JSONDecodeError, TypeError):
            pass

    if family == "github":
        # Stars-today (velocity) is a stronger trending signal than the
        # lifetime total; take whichever normalizes higher.
        today = _log_norm(engagement.get("stars_today", 0), 2.5)
        total = _log_norm(engagement.get("stars_total", article.trending_score), _SATURATION["github"])
        return max(today, total)

    value = (
        engagement.get("upvotes")
        or engagement.get("points")
        or article.trending_score
        or 0
    )
    return _log_norm(float(value), _SATURATION[family])


def recency(published_at: datetime, half_life_days: float) -> float:
    now = datetime.now(timezone.utc)
    pub = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - pub).total_seconds() / 86400)
    return math.exp(-age_days * math.log(2) / half_life_days)


def relevance_score(article: Article, window_days: int = 7) -> float:
    """Recency × popularity. The half-life scales with the browsing window:
    in a 30-day view a week-old item is still 'recent'; in a 1-day view it
    is ancient. Popularity floor keeps zero-vote items rankable, not zero."""
    half_life = max(1.0, window_days / 4)
    return recency(article.published_at, half_life) * (0.25 + 0.75 * popularity(article))


def _score_map(articles: list[Article], window_days: int) -> dict:
    """Relevance per article id, computed once — scoring involves a JSON
    parse of the engagement column, so the hot path must not repeat it
    inside every sort comparator."""
    return {a.id: relevance_score(a, window_days) for a in articles}


def apply_daily_caps(
    articles: list[Article],
    per_day: int = DEFAULT_PER_SOURCE_PER_DAY,
    window_days: int = 7,
    category_of: Optional[dict] = None,
) -> list[Article]:
    """Keep only the top-N most relevant items per source group per day.

    Group = source category when a mapping is provided (so 18 subreddits
    share one daily budget), else the source family prefix."""
    scores = _score_map(articles, window_days)
    buckets: dict = defaultdict(list)
    for a in articles:
        group = (category_of or {}).get(a.source_id) or _source_family(a.source_id)
        buckets[(group, a.published_at.date())].append(a)

    kept = []
    for bucket in buckets.values():
        bucket.sort(key=lambda a: scores[a.id], reverse=True)
        kept.extend(bucket[:per_day])

    kept.sort(key=lambda a: scores[a.id], reverse=True)
    return kept


def interleave_by_group(
    articles: list[Article],
    window_days: int = 7,
    category_of: Optional[dict] = None,
) -> list[Article]:
    """Round-robin across source groups within each publication day, newest
    day first — so the 'All' tab mixes arXiv/Reddit/GitHub instead of
    presenting one long column per source (app-feedback-v4)."""
    scores = _score_map(articles, window_days)
    by_day: dict = defaultdict(lambda: defaultdict(list))
    for a in articles:
        group = (category_of or {}).get(a.source_id) or _source_family(a.source_id)
        by_day[a.published_at.date()][group].append(a)

    result = []
    for day in sorted(by_day, reverse=True):
        groups = by_day[day]
        queues = [
            sorted(items, key=lambda a: scores[a.id], reverse=True)
            for items in groups.values()
        ]
        # Most relevant group leads each round
        queues.sort(key=lambda q: scores[q[0].id], reverse=True)
        i = 0
        while any(queues):
            for q in queues:
                if i < len(q):
                    result.append(q[i])
            i += 1
            if all(i >= len(q) for q in queues):
                break
    return result
