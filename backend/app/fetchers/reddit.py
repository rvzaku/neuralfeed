import asyncio
import time
import urllib.request

import feedparser
import structlog
from app.core.config import settings
from app.fetchers.base import BaseFetcher, FetchResult, fetch_with_backoff
from app.fetchers.rss import _strip_html

log = structlog.get_logger()

# Reddit rate-limits per client IP, not per subreddit — pace ALL reddit
# requests globally so concurrent sub fetches don't burst into a 429.
_PACE_SECONDS = 6.0  # Render's shared IP gets 429'd at 2.5s spacing
# Created lazily inside the running loop: on Python 3.9 a module-level
# asyncio.Lock() binds to whatever loop exists at import time, and pacing
# then crashes with "attached to a different loop" under asyncio.run()
_pace_lock: "asyncio.Lock | None" = None
_last_request = 0.0


async def _pace() -> None:
    global _last_request, _pace_lock
    if _pace_lock is None:
        _pace_lock = asyncio.Lock()
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
    # V7: topic-focused subs, gated by the same per-day relevance caps
    "reddit-mlscaling":       "mlscaling",
    "reddit-llmdevs":         "LLMDevs",
    "reddit-langchain":       "LangChain",
    "reddit-rag":             "Rag",
    "reddit-aiagents":        "AI_Agents",
    "reddit-computervision":  "computervision",
    "reddit-reinforcement":   "reinforcementlearning",
    "reddit-mlops":           "mlops",
}


_FAKE_THUMBS = {"self", "default", "nsfw", "spoiler", "image", ""}


def _reddit_image(post: dict) -> "str | None":
    """Preview image URL from the post JSON, filtering Reddit's pseudo-thumbnails
    (V6.1: junk thumbnails are noise, absence is the default)."""
    try:
        url = post["preview"]["images"][0]["source"]["url"]
        return url.replace("&amp;", "&")
    except (KeyError, IndexError, TypeError):
        pass
    thumb = post.get("thumbnail") or ""
    if thumb in _FAKE_THUMBS or not thumb.startswith("http"):
        return None
    return thumb


class RedditFetcher(BaseFetcher):
    def __init__(self, source_id: str, sub: "str | None" = None):
        self.source_id = source_id
        # Explicit sub for user-added custom sources; registry map otherwise
        self.sub = sub or SUBREDDITS.get(source_id)

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

    def _parse_listing(self, data: dict) -> list[dict]:
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
                "image_url": _reddit_image(post),
                "title": post.get("title", "").strip(),
                "url": url_out,
                "author": post.get("author"),
                "summary": summary or None,
                "published_at": None,  # will use epoch below
                "trending_score": float(post.get("score", 0)),
                "engagement": {
                    "upvotes": int(post.get("score", 0)),
                    "comments": int(post.get("num_comments", 0)),
                },
                "_created_utc": post.get("created_utc"),
            })

        # Convert epoch to ISO string for ingest layer
        from datetime import datetime, timezone
        for item in items:
            epoch = item.pop("_created_utc", None)
            if epoch:
                item["published_at"] = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        return items

    async def _fetch_listing(self, sub: str, path: str) -> "list[dict] | None":
        """One paced JSON listing request; None means blocked/failed."""
        url = f"https://www.reddit.com/r/{sub}/{path}"
        headers = {"User-Agent": settings.reddit_user_agent}
        try:
            await _pace()
            resp = await fetch_with_backoff(url, headers=headers)
            return self._parse_listing(resp.json())
        except Exception as e:  # FetchError is an Exception; one clause covers both
            log.warning("reddit_listing_failed", source_id=self.source_id, path=path, error=str(e))
            return None

    async def fetch(self) -> FetchResult:
        sub = self.sub
        if not sub:
            return FetchResult(source_id=self.source_id, error="unknown subreddit")

        # Blend hot (what's surging now) with top-of-week (what proved out) so
        # the relevance ranker has popularity signal, not just recency.
        hot = await self._fetch_listing(sub, "hot.json?limit=50")
        if hot is None:
            return await asyncio.to_thread(self._fetch_rss_fallback, sub)
        top_week = await self._fetch_listing(sub, "top.json?t=week&limit=25") or []

        seen, items = set(), []
        for item in hot + top_week:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            items.append(item)

        log.info("reddit_fetched", source_id=self.source_id, count=len(items))
        return FetchResult(source_id=self.source_id, items=items)

    async def backfill(self, days: int = 30) -> FetchResult:
        """Historical window via top.json — Reddit's only popularity-sorted
        lookback. t=month covers the 30-day target."""
        sub = self.sub
        if not sub:
            return FetchResult(source_id=self.source_id, error="unknown subreddit")
        t = "month" if days > 7 else "week"
        items = await self._fetch_listing(sub, f"top.json?t={t}&limit=100")
        if items is None:
            return await asyncio.to_thread(self._fetch_rss_fallback, sub)
        log.info("reddit_backfilled", source_id=self.source_id, count=len(items))
        return FetchResult(source_id=self.source_id, items=items)
