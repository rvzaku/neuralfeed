import asyncio
import xml.etree.ElementTree as ET
from app.core.config import settings
from app.fetchers.base import BaseFetcher, FetchResult
import httpx
import structlog

log = structlog.get_logger()

NS = "http://www.w3.org/2005/Atom"
QUERIES = {
    "arxiv-cs-ai": "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL",
    "arxiv-cs-cv": "cat:cs.CV+OR+stat.ML",
}


class ArxivFetcher(BaseFetcher):
    def __init__(self, source_id: str):
        self.source_id = source_id

    async def fetch(self) -> FetchResult:
        query = QUERIES.get(self.source_id, "cat:cs.AI")
        url = f"{settings.arxiv_api_base}?search_query={query}&sortBy=submittedDate&max_results=50"
        return await self._fetch_url(url)

    async def backfill(self, days: int = 30) -> FetchResult:
        """Pull the historical window in pages of 100 (arXiv etiquette: ≤3s
        between requests, modest page counts)."""
        from datetime import datetime, timedelta, timezone

        query = QUERIES.get(self.source_id, "cat:cs.AI")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y%m%d0000")
        end_date = datetime.now(timezone.utc).strftime("%Y%m%d2359")
        dated = f"{query}+AND+submittedDate:[{start_date}+TO+{end_date}]"

        all_items: list[dict] = []
        for start in (0, 100, 200, 300, 400):
            url = (
                f"{settings.arxiv_api_base}?search_query={dated}"
                f"&sortBy=submittedDate&start={start}&max_results=100"
            )
            result = await self._fetch_url(url)
            if not result.ok:
                if all_items:  # partial backfill is still useful
                    break
                return result
            all_items.extend(result.items)
            if len(result.items) < 100:
                break
            await asyncio.sleep(3)

        log.info("arxiv_backfilled", source_id=self.source_id, count=len(all_items))
        return FetchResult(source_id=self.source_id, items=all_items)

    async def _fetch_url(self, url: str) -> FetchResult:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
        except Exception as e:
            log.warning("arxiv_fetch_error", source_id=self.source_id, error=str(e))
            return FetchResult(source_id=self.source_id, error=str(e))

        items = []
        try:
            root = ET.fromstring(resp.text)
            for entry in root.findall(f"{{{NS}}}entry"):
                title_el = entry.find(f"{{{NS}}}title")
                id_el = entry.find(f"{{{NS}}}id")
                summary_el = entry.find(f"{{{NS}}}summary")
                published_el = entry.find(f"{{{NS}}}published")
                authors = entry.findall(f"{{{NS}}}author")

                if title_el is None or id_el is None:
                    continue

                abs_url = (id_el.text or "").strip()
                # Convert API id to abs URL: http://arxiv.org/abs/XXXX
                abs_url = abs_url.replace("http://arxiv.org/abs/", "https://arxiv.org/abs/")

                first_author = None
                if authors:
                    name_el = authors[0].find(f"{{{NS}}}name")
                    if name_el is not None:
                        first_author = name_el.text

                items.append({
                    "title": (title_el.text or "").strip().replace("\n", " "),
                    "url": abs_url,
                    "author": first_author,
                    "summary": (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else None,
                    "published_at": published_el.text if published_el is not None else None,
                    "trending_score": 0.0,
                })
        except ET.ParseError as e:
            return FetchResult(source_id=self.source_id, error=f"XML parse error: {e}")

        log.info("arxiv_fetched", source_id=self.source_id, count=len(items))
        return FetchResult(source_id=self.source_id, items=items)
