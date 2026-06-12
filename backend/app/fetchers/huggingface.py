from datetime import datetime, timezone
from typing import Optional
import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult

log = structlog.get_logger()


class HuggingFaceFetcher(BaseFetcher):
    source_id = "hf-models"

    async def fetch(self) -> FetchResult:
        url = "https://huggingface.co/api/models"
        params = {"sort": "lastModified", "limit": 30, "filter": "text-generation"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                models = resp.json()
        except Exception as e:
            log.warning("hf_fetch_error", error=str(e))
            return FetchResult(source_id=self.source_id, error=str(e))

        now = datetime.now(timezone.utc).isoformat()
        items = []
        for m in models:
            model_id = m.get("id", "")
            if not model_id:
                continue
            items.append({
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}",
                "author": model_id.split("/")[0] if "/" in model_id else None,
                "summary": (
                    f"New {(m.get('pipeline_tag') or 'AI').replace('-', ' ')} model "
                    f"on Hugging Face ({m.get('downloads', 0):,} downloads)."
                ),
                "published_at": m.get("createdAt") or m.get("lastModified") or now,
                "trending_score": float(m.get("downloads", 0)) / 1000.0,
                "engagement": {
                    "downloads": int(m.get("downloads", 0)),
                    "likes": int(m.get("likes", 0)),
                },
            })

        log.info("hf_fetched", count=len(items))
        return FetchResult(source_id=self.source_id, items=items)
