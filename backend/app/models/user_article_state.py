from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow


class UserArticleState(Base):
    """Per-user read/bookmark/feedback state (Phase 3.2). The legacy columns on
    Article remain the anonymous/single-user fallback."""

    __tablename__ = "user_article_state"

    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id"), primary_key=True
    )
    article_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("articles.id"), primary_key=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
