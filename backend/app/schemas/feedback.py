from typing import Literal
from pydantic import BaseModel


class FeedbackIn(BaseModel):
    article_id: str
    value: Literal[1, -1, 0]
