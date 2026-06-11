from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class SourceOut(BaseModel):
    id: str
    name: str
    category: str
    url: str
    access: str
    enabled: bool
    priority: str
    refresh_interval: str
    added_on: date
    last_fetched_at: Optional[datetime]
    signal_score: float
    notes: Optional[str]
    last_fetch_status: Optional[str] = None
    last_fetch_error: Optional[str] = None
    last_fetch_count: Optional[int] = None

    model_config = {"from_attributes": True}
