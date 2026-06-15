"""V6 Hotness Index — the flagship "what's hot right now" signal.

The user's mental model (app-feedback-v6): when OpenClaw launched, the whole
field lit up in a span of weeks — Moltbook, clawed board, everything dropped at
once and *everyone* was talking about it across every platform. NeuralFeed
should make that spike legible at a glance.

The basis (decision #2) is **cross-source velocity**: how many distinct sources
carry a story AND how fast it's spreading in the last 24–48h versus the steady
baseline. A story is "hot" only when it is BOTH spreading across sources and
recent — a 5-source story from three weeks ago is history, not heat. So recency
gates the score multiplicatively.

We deliberately surface heat as a *level* (0–3), rendered by the client as a
colour band rather than a raw number — a precise "0.62" is noise to a human;
"blazing" is signal (user's explicit ask for a colour scheme, not a score).
"""

import json
from typing import Optional

from app.models.article import Article
from app.services.relevance import _log_norm, _source_family, popularity, recency

# Hotness is a "right now" signal — its recency half-life is far shorter than the
# feed's relevance half-life so heat decays within a day or two, matching how the
# real conversation cools off after a launch week.
HEAT_HALF_LIFE_DAYS = 1.5

# Distinct-source coverage that counts as fully "spreading". Four independent
# sources carrying the same story in the window is strong cross-source velocity.
_FULL_SPREAD_SOURCES = 4.0

# Level thresholds on the 0..1 score. Below the first, no heat indicator shows —
# most of the feed is ordinary and should not be painted.
_LEVEL_THRESHOLDS = (0.18, 0.40, 0.62)  # → warm(1), hot(2), blazing(3)

HEAT_LABELS = {0: "", 1: "warm", 2: "hot", 3: "blazing"}


def _velocity(article: Article) -> float:
    """0..1 spread *rate* signal independent of cross-source count: GitHub
    stars-today and live discussion volume (comments) are how fast a single
    item is accelerating right now, distinct from lifetime popularity."""
    engagement: dict = {}
    if article.engagement:
        try:
            engagement = json.loads(article.engagement)
        except (json.JSONDecodeError, TypeError):
            pass

    signals = [0.0]
    if engagement.get("stars_today"):
        signals.append(_log_norm(engagement["stars_today"], 2.5))  # ~300/day = hot
    if engagement.get("comments"):
        # Discussion volume is the social analogue of "everyone's talking" —
        # ~500 comments saturates.
        signals.append(_log_norm(engagement["comments"], 2.7))
    if article.source_id.startswith("arxiv") and article.trending_score > 0:
        signals.append(_log_norm(article.trending_score, 2.0))
    return max(signals)


def hotness(article: Article, mentions: int = 1) -> float:
    """0..1 hotness from cross-source velocity, gated by recency.

    `mentions` is the distinct-source coverage count from
    `dedupe.cross_source_buzz` — the spine of the signal. Spread, per-item
    velocity, and popularity combine, then recency multiplies so only *current*
    spikes read as hot."""
    spread = min(max(mentions, 1) / _FULL_SPREAD_SOURCES, 1.0)
    vel = _velocity(article)
    pop = popularity(article)

    raw = 0.45 * spread + 0.35 * vel + 0.20 * pop
    rec = recency(article.published_at, HEAT_HALF_LIFE_DAYS)
    return round(rec * raw, 4)


def heat_level(score: float) -> int:
    """Map a 0..1 hotness score to a 0..3 colour band."""
    level = 0
    for threshold in _LEVEL_THRESHOLDS:
        if score >= threshold:
            level += 1
        else:
            break
    return level


def heat_for(article: Article, mentions: int = 1) -> "tuple[float, int]":
    """(score, level) convenience for the feed/topic display paths."""
    score = hotness(article, mentions)
    return score, heat_level(score)


def topic_heat(articles: list[Article], buzz: Optional[dict] = None) -> dict:
    """Per-topic-tag heat level (0..3) from the hottest few items carrying it.

    A topic is as hot as the spikes happening inside it — we take the mean of
    its top-3 item scores so one fluke doesn't paint a whole topic blazing, but
    a genuine multi-item surge (OpenClaw week) does.
    """
    buzz = buzz or {}
    by_tag: dict = {}
    for a in articles:
        score = hotness(a, buzz.get(a.id, 1))
        for tag in a.topic_tags or []:
            by_tag.setdefault(tag, []).append(score)

    heat: dict = {}
    for tag, scores in by_tag.items():
        top = sorted(scores, reverse=True)[:3]
        heat[tag] = heat_level(sum(top) / len(top))
    return heat
