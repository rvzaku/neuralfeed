"""Hacker News via the Algolia search API — an existing aggregator whose
votes/comments are a strong cross-community relevance signal (V7).

AI relevance is keyword-filtered client-side: Algolia's query matching is
loose, so we over-fetch front-page stories and keep the AI ones.
"""

import re
import time

import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult

log = structlog.get_logger()

_API = "https://hn.algolia.com/api/v1/search"

# Title must hit one of these to count as AI news
_AI_PATTERN = re.compile(
    r"\b(ai|llm|llms|gpt|claude|gemini|openai|anthropic|deepmind|deepseek|mistral|"
    r"machine learning|neural|transformer|diffusion|rag|agents?|chatbot|"
    r"language model|fine[- ]?tun\w*|inference|hugging ?face|pytorch|tensorflow|"
    r"stable diffusion|whisper|copilot|cuda|embedding|multimodal|qwen|llama)\b",
    re.IGNORECASE,
)
_MIN_POINTS = 20  # ignore stories that never got traction


def _parse_hits(hits: list[dict]) -> list[dict]:
    items = []
    for hit in hits:
        title = (hit.get("title") or "").strip()
        if not title or not _AI_PATTERN.search(title):
            continue
        points = int(hit.get("points") or 0)
        if points < _MIN_POINTS:
            continue
        hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        items.append({
            "title": title,
            "url": hit.get("url") or hn_url,
            "author": hit.get("author"),
            "summary": None,
            "published_at": hit.get("created_at"),
            "trending_score": float(points),
            "engagement": {
                "points": points,
                "comments": int(hit.get("num_comments") or 0),
            },
        })
    return items


class HackerNewsFetcher(BaseFetcher):
    source_id = "hackernews-ai"

    async def _search(self, params: dict) -> "list[dict] | None":
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(_API, params=params)
                resp.raise_for_status()
                return resp.json().get("hits", [])
        except Exception as e:
            log.warning("hackernews_fetch_error", error=str(e))
            return None

    async def fetch(self) -> FetchResult:
        return await self.backfill(days=3)

    async def backfill(self, days: int = 30) -> FetchResult:
        since = int(time.time()) - days * 86400
        all_items, seen = [], set()
        for page in range(3 if days > 7 else 1):
            hits = await self._search({
                "tags": "story",
                "numericFilters": f"created_at_i>{since},points>{_MIN_POINTS}",
                "hitsPerPage": 100,
                "page": page,
            })
            if hits is None:
                if all_items:
                    break
                return FetchResult(source_id=self.source_id, error="algolia request failed")
            for item in _parse_hits(hits):
                if item["url"] not in seen:
                    seen.add(item["url"])
                    all_items.append(item)
            if len(hits) < 100:
                break

        log.info("hackernews_fetched", count=len(all_items), window_days=days)
        return FetchResult(source_id=self.source_id, items=all_items)
