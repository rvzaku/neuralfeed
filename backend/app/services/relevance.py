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
    "editorial": 2.7,  # external HN/Reddit discussion of a blog post (~500 pts)
}
_EDITORIAL_BASELINE = 0.45  # blogs/newsletters/podcasts: curated, no votes
# arXiv papers are peer-curated and inherently selective — like editorial, the
# venue is itself a quality signal. Without this floor an untracted paper scores
# ~0 popularity and is structurally buried under every blog/podcast (which all
# get the editorial baseline), so the feed degenerates to "only blogs" no matter
# how much research is ingested (app-feedback-v6). Traction (HF Daily Papers)
# still lifts a paper above the floor.
_RESEARCH_BASELINE = 0.40

# --- Importance magnitude (long-horizon catch-up) ---------------------------
# `popularity()` is normalized *per source family* and saturates hard at 1.0, so
# a 7,470-point item and a 1,829-point item both read as "fully popular". That's
# fine for a freshness-led day/week feed (recency then differentiates), but it's
# fatal for Month/Year: every recent high-traction item ties at 1.0, recency
# always wins the tie, and the horizon can NEVER reach back to an older landmark
# — so Month and Year render identically (app-feedback-v7, repeat report).
#
# For the importance-led horizons we instead use a *magnitude-preserving* signal
# on a single GLOBAL log scale, so a genuinely bigger story (by absolute peak
# traction) outranks a smaller-but-newer one regardless of age. Editorial /
# research items keep a small floor so curated-but-untracted pieces stay
# rankable, but clearly below anything the community actually surfaced.
_GLOBAL_SATURATION = 4.0  # log10(10_000) — a landmark-scale story
_MAG_EDITORIAL_FLOOR = 0.20
_MAG_RESEARCH_FLOOR = 0.22


def _peak_engagement(article: Article) -> float:
    """Best single absolute traction number across the engagement metrics —
    the raw magnitude, before any per-family normalization."""
    engagement: dict = {}
    if article.engagement:
        try:
            engagement = json.loads(article.engagement)
        except (json.JSONDecodeError, TypeError):
            pass
    return max(
        float(engagement.get("upvotes", 0) or 0),
        float(engagement.get("points", 0) or 0) * 1.5,
        float(engagement.get("stars_today", 0) or 0),
        float(engagement.get("stars_total", 0) or 0),
        float(article.trending_score or 0),
    )


def importance_magnitude(article: Article) -> float:
    """0..1 absolute-traction magnitude on a single global log scale (no
    per-family saturation), with floors for curated sources. Used as the
    importance-led signal for Month/Year so older landmark items can outrank
    newer minor ones — the thing that makes the horizons genuinely differ."""
    mag = _log_norm(_peak_engagement(article), _GLOBAL_SATURATION)
    family = _source_family(article.source_id)
    if family == "arxiv":
        return max(_MAG_RESEARCH_FLOOR, mag)
    if family == "editorial":
        return max(_MAG_EDITORIAL_FLOOR, mag)
    return mag


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

    engagement: dict = {}
    if article.engagement:
        try:
            engagement = json.loads(article.engagement)
        except (json.JSONDecodeError, TypeError):
            pass

    if family == "editorial":
        # External traction (HN points + Reddit upvotes) when the wider
        # community picked the post up; otherwise the curated baseline — the
        # publication itself is the selectivity signal.
        external = float(engagement.get("points", 0)) * 1.5 + float(engagement.get("upvotes", 0))
        if external > 0:
            return max(_EDITORIAL_BASELINE, _log_norm(external, _SATURATION["editorial"]))
        return _EDITORIAL_BASELINE

    if family == "github":
        # Stars-today (velocity) is a stronger trending signal than the
        # lifetime total; take whichever normalizes higher.
        today = _log_norm(engagement.get("stars_today", 0), 2.5)
        total = _log_norm(engagement.get("stars_total", article.trending_score), _SATURATION["github"])
        return max(today, total)

    value = (
        engagement.get("upvotes")
        or engagement.get("points")
        or engagement.get("likes")
        or article.trending_score
        or 0
    )
    tracted = _log_norm(float(value), _SATURATION[family])
    if family == "arxiv":
        # Selective venue → never below the research baseline; traction lifts it.
        return max(_RESEARCH_BASELINE, tracted)
    return tracted


def recency(published_at: datetime, half_life_days: float) -> float:
    now = datetime.now(timezone.utc)
    pub = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - pub).total_seconds() / 86400)
    return math.exp(-age_days * math.log(2) / half_life_days)


def _half_life(window_days: int) -> float:
    """Recency half-life for the browsing window. Tuned short (window/6) so the
    feed leads with FRESH content — newly published items outrank older ones —
    while popularity still differentiates among items of similar age (freshness
    first, but still relevant). A 30-day view stays lenient; a 1-day view is
    strict. Used by both the score and the displayed match %, so order and
    label never diverge."""
    return max(0.75, window_days / 6)


def importance_weight(window_days: int) -> float:
    """How much the score should lean on *importance* (recency-independent
    popularity/traction) vs. *freshness* — as a function of the browsing horizon.

    The user's "catch me up over any window" requirement (app-feedback-v7): opening
    the app a year later must surface the year's LANDMARK items (an OpenClaw-scale
    launch), not merely last week's minor news. So recency dominates a day view and
    nearly vanishes over a year. Short windows (≤7d) keep the original freshness-led
    behavior exactly (weight 0), so day/week feeds are unchanged."""
    if window_days <= 7:
        return 0.0
    if window_days <= 30:
        return 0.45
    if window_days <= 90:
        return 0.65
    return 0.85


def _relevance_unit(article: Article, window_days: int = 7) -> float:
    """Core 0..1 score shared by ranking and the displayed match %, so the two can
    never diverge. Blends a freshness-led term (recency × popularity) with an
    importance-led term (popularity alone) by the horizon's `importance_weight`."""
    pop = popularity(article)
    rec = recency(article.published_at, _half_life(window_days))
    fresh_led = rec * (0.25 + 0.75 * pop)   # original behavior (freshness first)
    beta = importance_weight(window_days)
    if beta == 0.0:
        # Short horizons (≤7d) are freshness-led, exactly as before — no change.
        return fresh_led
    # Long horizons: the importance term uses the magnitude-preserving signal (not
    # the saturated per-family popularity) so a bigger older story can outrank a
    # smaller newer one and Month/Year genuinely reach back (app-feedback-v7).
    importance_led = 0.15 + 0.85 * importance_magnitude(article)
    return (1.0 - beta) * fresh_led + beta * importance_led


def relevance_score(article: Article, window_days: int = 7) -> float:
    """Horizon-aware relevance. For short windows this is recency × popularity
    (freshness-led, unchanged); for long windows it shifts to importance-led so
    landmark items survive months/years of age. Popularity floor keeps zero-vote
    items rankable, not zero."""
    return _relevance_unit(article, window_days)


_FAMILY_LABEL = {"reddit": "Reddit", "hackernews": "Hacker News", "github": "GitHub",
                 "hf": "Hugging Face", "arxiv": "arXiv"}


def explain(
    article: Article,
    window_days: int = 7,
    topic_weights: Optional[dict] = None,
    source_affinity: Optional[dict] = None,
    mentions: int = 1,
) -> "tuple[int, list[str]]":
    """(match 0-100, human reasons) — the v5 'why am I seeing this' line.
    Reasons lead with traction (proof it isn't junk), then personal fit.

    `mentions` is the cross-source coverage count (V6): a story carried by
    several independent sources is genuinely gaining traction, so it earns a
    leading reason and a bounded match boost."""
    # Cross-source coverage is hard proof of traction — lift match up to +12
    buzz_boost = min(max(mentions - 1, 0) * 6, 12)
    # Same horizon-aware core the ranking uses, so match % and sort order align.
    match = min(100, int(round(100 * _relevance_unit(article, window_days))) + buzz_boost)

    engagement: dict = {}
    if article.engagement:
        try:
            engagement = json.loads(article.engagement)
        except (json.JSONDecodeError, TypeError):
            pass

    family = _source_family(article.source_id)
    reasons: list[str] = []

    if mentions >= 2:
        reasons.append(f"covered by {mentions} sources")
    if engagement.get("stars_today"):
        reasons.append(f"+{engagement['stars_today']:,} stars today")
    elif engagement.get("stars_total"):
        reasons.append(f"{engagement['stars_total']:,} stars")
    # HN points are a distinct, named signal (esp. for editorial posts the
    # community surfaced) — don't fold them into a generic "upvotes" line.
    if engagement.get("points"):
        reasons.append(f"{engagement['points']:,} points on Hacker News")
    if engagement.get("upvotes"):
        # For editorial posts the upvotes came from Reddit; native social
        # sources name their own platform.
        platform = "Reddit" if family == "editorial" else _FAMILY_LABEL.get(family, "the source")
        reasons.append(f"{engagement['upvotes']:,} upvotes on {platform}")
    if engagement.get("comments"):
        reasons.append(f"{engagement['comments']:,} comments")
    if family == "arxiv" and article.trending_score > 0:
        reasons.append("trending on HF Daily Papers")

    liked_tags = [
        t.replace("-", " ") for t in (article.topic_tags or [])
        if (topic_weights or {}).get(t, 0) > 0.1
    ]
    if liked_tags:
        reasons.append(f"matches topics you like: {', '.join(liked_tags[:2])}")
    if (source_affinity or {}).get(article.source_id, 0) > 0.1:
        reasons.append("from a source you often like")

    age_hours = (datetime.now(timezone.utc) - (
        article.published_at if article.published_at.tzinfo
        else article.published_at.replace(tzinfo=timezone.utc)
    )).total_seconds() / 3600
    if age_hours < 24:
        reasons.append("published today")

    return match, reasons[:3]


def score_map(articles: list[Article], window_days: int) -> dict:
    """Relevance per article id, computed once — scoring involves a JSON
    parse of the engagement column, so the hot path must not repeat it
    inside every sort comparator. Pass the result into apply_daily_caps /
    interleave_by_group to score each article a single time per request."""
    return {a.id: relevance_score(a, window_days) for a in articles}


# Back-compat alias: the underscore name was the original private API.
_score_map = score_map


def apply_daily_caps(
    articles: list[Article],
    per_day: int = DEFAULT_PER_SOURCE_PER_DAY,
    window_days: int = 7,
    category_of: Optional[dict] = None,
    scores: Optional[dict] = None,
) -> list[Article]:
    """Keep only the top-N most relevant items per source group per day.

    Group = source category when a mapping is provided (so 18 subreddits
    share one daily budget), else the source family prefix.

    `scores` may be a precomputed id→relevance map (keyed for at least every
    article here) to avoid re-parsing the engagement JSON the caller already
    scored — pass None to compute it locally."""
    if scores is None:
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


def interleave_by_importance(
    articles: list[Article],
    window_days: int = 7,
    category_of: Optional[dict] = None,
    scores: Optional[dict] = None,
    group_cap: int = 3,
) -> list[Article]:
    """Catch-up ordering for the Month/Year horizons (app-feedback-v7).

    **Score-first, with a soft per-group cap.** An earlier version round-robined
    one item per source group per round; that guaranteed diversity but flattened
    the horizon difference — the top-N became "the #1 of each group", which is
    almost the same recent set for Month and Year, and it buried older landmark
    items below newer minor ones. Here items are ordered strictly by the
    (magnitude-led) importance score, so a months-old landmark leads a Year view;
    a per-group cap (default 3) is the only constraint, so one family still can't
    monopolize the shortlist. Items past the cap are appended in score order so
    nothing is dropped — the cap only shapes the *head* of the list, which is all
    the finite Feed shows.

    Pairs with importance-led candidate selection in the API layer (the candidate
    pool for long horizons is drawn by traction, not pure recency) so older
    landmarks are actually in the pool to be ranked."""
    if scores is None:
        scores = _score_map(articles, window_days)

    ordered = sorted(articles, key=lambda a: scores[a.id], reverse=True)
    primary: list[Article] = []
    deferred: list[Article] = []
    counts: dict = defaultdict(int)
    for a in ordered:
        group = (category_of or {}).get(a.source_id) or _source_family(a.source_id)
        if counts[group] < group_cap:
            primary.append(a)
            counts[group] += 1
        else:
            deferred.append(a)
    return primary + deferred


def interleave_by_group(
    articles: list[Article],
    window_days: int = 7,
    category_of: Optional[dict] = None,
    scores: Optional[dict] = None,
) -> list[Article]:
    """Round-robin across source groups within each publication day, newest
    day first — so the 'All' tab mixes arXiv/Reddit/GitHub instead of
    presenting one long column per source (app-feedback-v4).

    `scores`: optional precomputed id→relevance map, reused from the caller."""
    if scores is None:
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
