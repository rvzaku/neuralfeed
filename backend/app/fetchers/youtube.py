import feedparser
import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult
from app.fetchers.rss import _strip_html

log = structlog.get_logger()

# channel_id -> display name
CHANNELS = {
    "UCbmNph6atAoGfqLoCL_duAg": "Andrej Karpathy",
    "UCbfYPyITQ-7l4upoX8nvctg": "Two Minute Papers",
    "UC9-y-6csu5WGm29I7JiwpnA": "Computerphile",
    "UCWX3yGbODI3RQUgFnOOGjbg": "Yannic Kilcher",
    "UCnUYZLuoy1rq1aVMwx4aTzw": "AI Explained",
    "UCSHZKyawb77ixDdsGog4iWA": "Lex Fridman",
    "UCTkXRDQl0luXxVQrRQvWS6w": "Matthew Berman",
    "UCfzlCWGWYyIQ0aLC5w48gBQ": "Sentdex",
}


class YouTubeFetcher(BaseFetcher):
    source_id = "youtube-ai"

    async def fetch(self) -> FetchResult:
        all_items: list = []
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for channel_id, channel_name in CHANNELS.items():
                url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:5]:
                        link = entry.get("link", "")
                        if not link:
                            continue
                        all_items.append({
                            "title": _strip_html(entry.get("title", "")),
                            "url": link,
                            "author": channel_name,
                            "summary": _strip_html(entry.get("summary", ""))[:500] or None,
                            "published_at": entry.get("published"),
                            "trending_score": 0.0,
                        })
                except Exception as e:
                    log.warning("youtube_fetch_error", channel=channel_name, error=str(e))

        log.info("youtube_fetched", count=len(all_items))
        return FetchResult(source_id=self.source_id, items=all_items)
