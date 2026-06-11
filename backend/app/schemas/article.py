from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ArticleOut(BaseModel):
    id: str
    title: str
    url: str
    source_id: str
    author: Optional[str]
    summary: Optional[str]
    published_at: datetime
    fetched_at: datetime
    topic_tags: list[str]
    is_read: bool
    is_bookmarked: bool
    feedback: Optional[int]
    trending_score: float

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    limit: int
    has_more: bool
