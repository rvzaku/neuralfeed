from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class FeedbackLog(Base):
    __tablename__ = "feedback_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)  # +1 or -1
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
