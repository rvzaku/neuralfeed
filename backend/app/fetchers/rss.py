import re
from typing import Optional
import feedparser
import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult

log = structlog.get_logger()

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text).strip()


RSS_SOURCES = {
    # Company blogs — Phase 1
    "rss-openai":             "https://openai.com/blog/rss.xml",
    # Anthropic publishes no RSS; community-maintained mirror of anthropic.com/news
    "rss-anthropic":          "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
    "rss-deepmind":           "https://deepmind.google/blog/rss.xml",
    "rss-huggingface":        "https://huggingface.co/blog/feed.xml",
    # ai.meta.com/blog has no feed; engineering.fb.com carries the AI posts
    "rss-metaai":             "https://engineering.fb.com/feed/",
    # Company blogs — Phase 2
    "rss-googleai":           "https://blog.research.google/feeds/posts/default",
    "rss-msresearch":         "https://www.microsoft.com/en-us/research/feed/",
    "rss-mistral":            "https://mistral.ai/rss.xml",
    "rss-appleml":            "https://machinelearning.apple.com/rss.xml",
    "rss-awsai":              "https://aws.amazon.com/blogs/machine-learning/feed/",
    "rss-eleutherai":         "https://blog.eleuther.ai/index.xml",
    # Disabled in seed (no working feed as of 2026-06-11): rss-cohere, rss-stability,
    # rss-ai2, rss-deepseek — kept in the registry with notes, never deleted.
    "rss-cohere":             "https://cohere.com/blog/rss.xml",
    "rss-stability":          "https://stability.ai/news?format=rss",
    "rss-ai2":                "https://medium.com/feed/ai2-blog",
    "rss-deepseek":           "https://api.deepseek.com/blog/rss",
    # Newsletters — Phase 1
    "newsletter-batch":       "https://www.deeplearning.ai/the-batch/feed/",
    "newsletter-importai":    "https://importai.substack.com/feed",
    "newsletter-tldr":        "https://tldr.tech/api/rss/ai",
    "newsletter-aheadofai":   "https://magazine.sebastianraschka.com/feed",
    "newsletter-lastweekai":  "https://lastweekin.ai/feed",
    # Newsletters — Phase 2
    "newsletter-decoder":     "https://the-decoder.com/feed/",
    "newsletter-gradientflow": "https://gradientflow.com/feed/",
    "newsletter-aiedge":      "https://newsletter.theaiedge.io/feed",
    "newsletter-alphasignal": "https://alphasignal.ai/rss",
    "newsletter-algbridge":   "https://thealgorithmicbridge.substack.com/feed",
    "newsletter-davissummarizes": "https://dblalock.substack.com/feed",
    # Podcasts
    "podcast-lexfridman":     "https://lexfridman.com/feed/podcast/",
    "podcast-twiml":          "https://twimlai.com/feed",
    "podcast-practicalai":    "https://changelog.com/practicalai/feed",
    "podcast-nopriors":       "https://feeds.megaphone.fm/nopriors",
    "podcast-eyeonai":        "https://aneyeonai.libsyn.com/rss",
    "podcast-gradient":       "https://thegradientpub.substack.com/feed",
    # Funding / business
    "rss-techcrunch-ai":      "https://techcrunch.com/category/artificial-intelligence/feed/",
    "rss-venturebeat-ai":     "https://venturebeat.com/category/ai/feed/",
}


class RSSFetcher(BaseFetcher):
    def __init__(self, source_id: str, feed_url: Optional[str] = None):
        self.source_id = source_id
        self.feed_url = feed_url or RSS_SOURCES.get(source_id, "")

    async def fetch(self) -> FetchResult:
        if not self.feed_url:
            return FetchResult(source_id=self.source_id, error="no feed URL configured")

        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                resp = await client.get(
                    self.feed_url,
                    headers={"User-Agent": "NeuralFeed/0.1 (RSS reader)"},
                )
                resp.raise_for_status()
                raw_content = resp.text
        except Exception as e:
            log.warning("rss_fetch_error", source_id=self.source_id, error=str(e))
            return FetchResult(source_id=self.source_id, error=str(e))

        feed = feedparser.parse(raw_content)
        items = []
        for entry in feed.entries:
            link = entry.get("link", "").strip()
            if not link:
                continue

            summary_raw = entry.get("summary") or entry.get("content", [{}])[0].get("value", "")
            summary = _strip_html(summary_raw)[:500] or None

            published = None
            if hasattr(entry, "published"):
                published = entry.published
            elif hasattr(entry, "updated"):
                published = entry.updated

            items.append({
                "title": _strip_html(entry.get("title", "")).strip(),
                "url": link,
                "author": entry.get("author"),
                "summary": summary,
                "published_at": published,
                "trending_score": 0.0,
            })

        log.info("rss_fetched", source_id=self.source_id, count=len(items))
        return FetchResult(source_id=self.source_id, items=items)
