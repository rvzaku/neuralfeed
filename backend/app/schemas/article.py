import json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

# Upper bounds per engagement metric — anything above is corrupt data (e.g. a
# GitHub star count that swallowed inline-SVG path digits during scraping).
# Clamped at read time so historical garbage in the DB never reaches the UI,
# with no migration or refetch needed.
_ENGAGEMENT_CAPS = {
    "stars_total": 50_000_000,
    "stars_today": 1_000_000,
    "forks": 10_000_000,
    "upvotes": 10_000_000,
    "points": 1_000_000,
    "comments": 1_000_000,
    "downloads": 10_000_000_000,
    "likes": 50_000_000,
}


class ArticleOut(BaseModel):
    id: str
    title: str
    url: str
    source_id: str
    author: Optional[str]
    summary: Optional[str]
    image_url: Optional[str] = None
    published_at: datetime
    fetched_at: datetime
    topic_tags: list[str]
    is_read: bool
    is_bookmarked: bool
    feedback: Optional[int]
    trending_score: float
    engagement: Optional[dict] = None
    engagement_at: Optional[datetime] = None
    context_line: Optional[str] = None
    original_title: Optional[str] = None
    # V8: visible relevance — match percentage + human-readable reasons
    relevance: Optional[int] = None
    why: Optional[list[str]] = None
    # V6 Hotness Index — cross-source velocity rendered as a 0..3 colour band
    # ("warm"/"hot"/"blazing"). `hotness` is the raw 0..1 score for ordering;
    # `heat` is the band the client paints. Both are ranked-view only.
    hotness: Optional[float] = None
    heat: Optional[int] = None

    @field_validator("image_url", mode="before")
    @classmethod
    def _safe_image_url(cls, v):
        # Only ever hand the client a hotlinkable http(s) image URL — never a
        # data:/javascript:/relative value that could be abused on render.
        if isinstance(v, str) and v.startswith(("http://", "https://")):
            return v
        return None

    @field_validator("engagement", mode="before")
    @classmethod
    def _parse_engagement(cls, v):
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        if not isinstance(v, dict):
            return v
        cleaned: dict = {}
        for key, val in v.items():
            cap = _ENGAGEMENT_CAPS.get(key)
            if cap is not None:
                # Drop non-numeric or implausible counts rather than show them
                try:
                    num = int(val)
                except (TypeError, ValueError):
                    continue
                if num < 0 or num > cap:
                    continue
                cleaned[key] = num
            else:
                cleaned[key] = val
        return cleaned or None

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    limit: int
    has_more: bool
    # V7-6: the effective feed-density (visible feed length). Lets the client
    # number 1..N and decide whether to show a "Show more" affordance.
    density: int = 0
