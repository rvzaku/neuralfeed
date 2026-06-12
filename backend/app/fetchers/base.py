import asyncio
from dataclasses import dataclass, field
from typing import Optional, TypedDict

import httpx
import structlog

log = structlog.get_logger()

RETRYABLE_STATUSES = {429, 503}
DEFAULT_BACKOFFS = (1.0, 4.0, 15.0)  # seconds between attempts


class RawItem(TypedDict, total=False):
    """Contract every fetcher's items must follow. Only ingest parses dates."""

    title: str
    url: str
    author: Optional[str]
    summary: Optional[str]
    published_at: Optional[str]  # ISO string or None; ingest normalizes
    trending_score: float
    engagement: Optional[dict]  # platform stats: stars/upvotes/comments/points


class FetchError(Exception):
    """Raised when a fetch fails after retries or with a non-retryable status."""


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

    async def backfill(self, days: int = 30) -> FetchResult:
        """Fetch a historical window. Fetchers without a date-windowed API
        (RSS feeds, scrapes) fall back to a regular fetch."""
        return await self.fetch()


async def fetch_with_backoff(
    url: str,
    *,
    headers: Optional[dict] = None,
    client: Optional[httpx.AsyncClient] = None,
    backoffs: tuple = DEFAULT_BACKOFFS,
    timeout: float = 20.0,
) -> httpx.Response:
    """GET with exponential backoff on 429/503, honoring Retry-After.

    Attempts = len(backoffs) + 1. Raises FetchError on a non-retryable
    status or once retries are exhausted.
    """
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=timeout, follow_redirects=True)
    try:
        last_status: Optional[int] = None
        for attempt, delay in enumerate((*backoffs, None)):
            resp = await client.get(url, headers=headers)
            if resp.status_code < 400:
                return resp
            last_status = resp.status_code
            if resp.status_code not in RETRYABLE_STATUSES or delay is None:
                break
            retry_after = resp.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
            log.warning("fetch_retrying", url=url, status=resp.status_code,
                        attempt=attempt + 1, wait=wait)
            await asyncio.sleep(wait)
        raise FetchError(f"GET {url} failed with HTTP {last_status}")
    finally:
        if owns_client:
            await client.aclose()
