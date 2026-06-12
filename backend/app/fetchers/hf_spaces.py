from datetime import datetime, timezone

import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult

log = structlog.get_logger()


class HFSpacesFetcher(BaseFetcher):
    """Trending Hugging Face Spaces — the 'products' bucket's demo/tool signal."""

    source_id = "hf-spaces"

    async def fetch(self) -> FetchResult:
        url = "https://huggingface.co/api/spaces"
        params = {"sort": "trendingScore", "limit": 30, "full": "true"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                spaces = resp.json()
        except Exception as e:
            log.warning("hf_spaces_fetch_error", error=str(e))
            return FetchResult(source_id=self.source_id, error=str(e))

        now = datetime.now(timezone.utc).isoformat()
        items = []
        for s in spaces:
            space_id = s.get("id", "")
            if not space_id:
                continue
            card = s.get("cardData") or {}
            desc = (card.get("short_description") or "").strip()
            likes = s.get("likes", 0)
            summary = (
                f"{desc} — community demo on Hugging Face ({likes:,} likes)."
                if desc
                else f"Interactive AI demo on Hugging Face ({likes:,} likes)."
            )
            items.append({
                "title": card.get("title") or space_id,
                "url": f"https://huggingface.co/spaces/{space_id}",
                "author": space_id.split("/")[0] if "/" in space_id else None,
                "summary": summary,
                "published_at": s.get("createdAt") or s.get("lastModified") or now,
                "trending_score": float(s.get("likes", 0)),
                "engagement": {"likes": int(s.get("likes", 0))},
            })

        log.info("hf_spaces_fetched", count=len(items))
        return FetchResult(source_id=self.source_id, items=items)
