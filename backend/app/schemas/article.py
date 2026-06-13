import json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


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
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    limit: int
    has_more: bool
