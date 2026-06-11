from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Boolean, Float, Date, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    access: Mapped[str] = mapped_column(String(16), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(8), default="medium", nullable=False)
    refresh_interval: Mapped[str] = mapped_column(String(16), default="daily", nullable=False)
    added_on: Mapped[date] = mapped_column(Date, nullable=False)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    signal_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_fetch_status: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)  # ok | error
    last_fetch_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_fetch_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Refresh cursor: stamped before fetching so a crash still advances ordering
    fetch_attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
