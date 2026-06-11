from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FetchResult:
    source_id: str
    items: list = field(default_factory=list)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


class BaseFetcher:
    source_id: str

    async def fetch(self) -> FetchResult:
        raise NotImplementedError
