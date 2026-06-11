from datetime import date
from typing import Optional
from sqlalchemy import String, Boolean, Date, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class WatchedAccount(Base):
    __tablename__ = "watched_accounts"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # "{platform}:{handle}"
    platform: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # twitter|linkedin|youtube
    handle: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    source_of_discovery: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    added_on: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
