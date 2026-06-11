import asyncio
import time
import urllib.request

import feedparser
import structlog
from app.core.config import settings
from app.fetchers.base import BaseFetcher, FetchError, FetchResult, fetch_with_backoff
from app.fetchers.rss import _strip_html

log = structlog.get_logger()

# Reddit rate-limits per client IP, not per subreddit — pace ALL reddit
# requests globally so concurrent sub fetches don't burst into a 429.
_PACE_SECONDS = 2.5
_pace_lock = asyncio.Lock()
_last_request = 0.0


async def _pace() -> None:
    global _last_request
    async with _pace_lock:
        wait = _last_request + _PACE_SECONDS - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request = time.monotonic()

SUBREDDITS = {
    "reddit-ml":              "MachineLearning",
    "reddit-localllama":      "LocalLLaMA",
    "reddit-artificial":      "artificial",
    "reddit-singularity":     "singularity",
    "reddit-chatgpt":         "ChatGPT",
    "reddit-claudeai":        "ClaudeAI",
    "reddit-openai":          "OpenAI",
    "reddit-stablediffusion": "StableDiffusion",
    "reddit-learnml":         "learnmachinelearning",
    "reddit-deeplearning":    "deeplearning",
}


class RedditFetcher(BaseFetcher):
    def __init__(self, source_id: str):
        self.source_id = source_id

    def _fetch_rss_fallback(self, sub: str) -> FetchResult:
        """Reddit blocks httpx's TLS fingerprint on many networks but serves
        hot.rss to urllib. Loses score/selftext but keeps the feed alive."""
        url = f"https://www.reddit.com/r/{sub}/hot.rss?limit=50"
        req = urllib.request.Request(url, headers={"User-Agent": settings.reddit_user_agent})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            log.warning("reddit_rss_fallback_error", source_id=self.source_id, error=str(e))
            return FetchResult(source_id=self.source_id, error=f"json+rss both failed: {e}")

        items = []
        for entry in feedparser.parse(body).entries:
            link = entry.get("link", "").strip()
            if not link:
                continue
            items.append({
                "title": _strip_html(entry.get("title", "")).strip(),
                "url": link,
                "author": (entry.get("author") or "").lstrip("/u/") or None,
                "summary": None,  # RSS body is rendered HTML, not the selftext snippet
                "published_at": entry.get("published") or entry.get("updated"),
                "trending_score": 0.0,
            })
        log.info("reddit_fetched_rss_fallback", source_id=self.source_id, count=len(items))
        return FetchResult(source_id=self.source_id, items=items)

    async def fetch(self) -> FetchResult:
        sub = SUBREDDITS.get(self.source_id)
        if not sub:
            return FetchResult(source_id=self.source_id, error="unknown subreddit")

        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=50"
        headers = {"User-Agent": settings.reddit_user_agent}
        try:
            await _pace()
            resp = await fetch_with_backoff(url, headers=headers)
            data = resp.json()
        except (FetchError, Exception) as e:
            log.warning("reddit_json_blocked_trying_rss", source_id=self.source_id, error=str(e))
            return await asyncio.to_thread(self._fetch_rss_fallback, sub)

        items = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            if post.get("stickied"):
                continue

            # Link posts go to external URL; self posts go to reddit permalink
            is_self = post.get("is_self", False)
            url_out = f"https://reddit.com{post['permalink']}" if is_self else post.get("url", "")
            if not url_out:
                continue

            summary = post.get("selftext", "")[:500] if is_self else None
            items.append({
                "title": post.get("title", "").strip(),
                "url": url_out,
                "author": post.get("author"),
                "summary": summary or None,
                "published_at": None,  # will use epoch below
                "trending_score": float(post.get("score", 0)),
                "_created_utc": post.get("created_utc"),
            })

        # Convert epoch to ISO string for ingest layer
        from datetime import datetime, timezone
        for item in items:
            epoch = item.pop("_created_utc", None)
            if epoch:
                item["published_at"] = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()

        log.info("reddit_fetched", source_id=self.source_id, count=len(items))
        return FetchResult(source_id=self.source_id, items=items)
