import hashlib
import re
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Float, DateTime, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

_STOP_WORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "is", "are",
    "was", "were", "with", "and", "or", "but", "by", "from", "as", "it",
}
_NON_WORD = re.compile(r"[^\w\s]")


def make_article_id(source_id: str, url: str) -> str:
    return hashlib.sha256(f"{source_id}:{url}".encode()).hexdigest()[:16]


def make_title_hash(title: str) -> str:
    """Normalize title and hash for fuzzy duplicate detection across URL variants."""
    normalized = _NON_WORD.sub("", title.lower())
    words = sorted(w for w in normalized.split() if w not in _STOP_WORDS)
    return hashlib.sha256(" ".join(words).encode()).hexdigest()[:16]


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    author: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Preview image URL (hotlinked, never stored as a file — V6)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    topic_tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trending_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    title_hash: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, index=True)
    # Cached AI summary as JSON {"summary": str, "takeaways": [str]} — our own
    # derivative work; full article text is never stored (see CLAUDE.md).
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Deep "10-minute read" markdown brief — same derivative-only rule applies
    ai_deep_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_deep_summary_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Engagement metadata from the original platform, JSON-encoded string:
    # {"stars_total": int, "stars_today": int, "upvotes": int, "comments": int,
    #  "points": int} — keys present only when the source provides them.
    # Text (not JSON type) so the additive-column boot migration stays portable.
    engagement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # One-line LLM "why this matters" context, cached forever once generated
    context_line: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Slug/raw title as fetched, kept when the enricher rewrites `title` (V8)
    original_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
