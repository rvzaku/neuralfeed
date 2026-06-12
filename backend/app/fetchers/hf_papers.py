"""Hugging Face Daily Papers — community-curated trending arXiv papers.

Double duty (V7): a source in its own right, and the traction signal that
lets the feed show only arXiv papers people actually care about (ingest
boosts the matching arxiv-* article's trending_score).
"""

import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult

log = structlog.get_logger()

_API = "https://huggingface.co/api/daily_papers"


def _parse_papers(data: list) -> list[dict]:
    items = []
    for entry in data:
        paper = entry.get("paper") or {}
        arxiv_id = paper.get("id")
        title = (paper.get("title") or "").strip().replace("\n", " ")
        if not arxiv_id or not title:
            continue
        upvotes = int(paper.get("upvotes") or 0)
        items.append({
            "title": title,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "author": (paper.get("authors") or [{}])[0].get("name"),
            "summary": (paper.get("summary") or "").strip().replace("\n", " ") or None,
            "published_at": paper.get("publishedAt") or entry.get("publishedAt"),
            "trending_score": float(upvotes),
            "engagement": {"upvotes": upvotes, "comments": int(entry.get("numComments") or 0)},
        })
    return items


class HFPapersFetcher(BaseFetcher):
    source_id = "hf-papers"

    async def _get(self, client: httpx.AsyncClient, params: dict) -> "list | None":
        try:
            resp = await client.get(_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else None
        except Exception as e:
            log.warning("hf_papers_fetch_error", params=params, error=str(e))
            return None

    async def fetch(self) -> FetchResult:
        async with httpx.AsyncClient(timeout=20) as client:
            data = await self._get(client, {"limit": 50})
        if data is None:
            return FetchResult(source_id=self.source_id, error="daily_papers request failed")
        items = _parse_papers(data)
        log.info("hf_papers_fetched", count=len(items))
        return FetchResult(source_id=self.source_id, items=items)

    async def backfill(self, days: int = 30) -> FetchResult:
        """Daily papers are published per weekday — walk the window day by day."""
        items, seen = [], set()
        today = datetime.now(timezone.utc).date()
        async with httpx.AsyncClient(timeout=20) as client:
            for offset in range(days):
                day = today - timedelta(days=offset)
                if day.weekday() >= 5:  # no daily papers on weekends
                    continue
                data = await self._get(client, {"date": day.isoformat(), "limit": 50})
                for item in _parse_papers(data or []):
                    if item["url"] not in seen:
                        seen.add(item["url"])
                        items.append(item)
                await asyncio.sleep(0.5)

        if not items:
            return FetchResult(source_id=self.source_id, error="daily_papers backfill empty")
        log.info("hf_papers_backfilled", count=len(items), window_days=days)
        return FetchResult(source_id=self.source_id, items=items)
