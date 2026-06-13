import re
from typing import Optional
import feedparser
import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult

log = structlog.get_logger()

_TAG_RE = re.compile(r"<[^>]+>")


_IMG_SRC_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


def _rss_image(entry) -> "str | None":
    """media:content / media:thumbnail / image enclosure → URL, else the first
    inline <img> in the entry HTML. Returns a hotlinkable URL or None — the
    image file is never stored, only its source URL (CLAUDE.md)."""
    for media in entry.get("media_content", []) or []:
        url = media.get("url")
        if url and media.get("medium", "image") == "image":
            return url
    for thumb in entry.get("media_thumbnail", []) or []:
        if thumb.get("url"):
            return thumb["url"]
    for enc in entry.get("enclosures", []) or []:
        if enc.get("href") and "image" in (enc.get("type") or ""):
            return enc["href"]
    # Many blog feeds embed the hero image inline in the content HTML
    html = entry.get("content", [{}])[0].get("value", "") or entry.get("summary", "")
    m = _IMG_SRC_RE.search(html or "")
    if m and m.group(1).startswith("http"):
        return m.group(1)
    return None


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text).strip()


_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def _concise_title(raw_title: str, fallback_summary: Optional[str] = None) -> str:
    """A short, scannable headline from a possibly-verbose entry title.

    LinkedIn (via RSSHub) and some feeds use the entire post body as the title,
    which floods the card. Take the first sentence/line, drop a trailing colon,
    and cap length — the full text still lives in `summary`."""
    text = _strip_html(raw_title or "").replace("\n", " ").strip()
    if not text:
        text = _strip_html(fallback_summary or "").strip()
    # First sentence or first line, whichever comes first
    first = _SENTENCE_END_RE.split(text, maxsplit=1)[0].strip()
    if len(first) > 100:
        # No sentence break early enough — cut on a word boundary
        first = first[:97].rsplit(" ", 1)[0].rstrip(",;:—- ") + "…"
    return first or text[:100]


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
    # LinkedIn (V9) — ToS-safe proxy: Google News indexes public LinkedIn
    # posts/articles; we read Google's RSS, never touch LinkedIn itself
    "linkedin-pulse":         "https://news.google.com/rss/search?q=site%3Alinkedin.com%20(AI%20OR%20LLM%20OR%20%22machine%20learning%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en",
    # Conferences (V4)
    "conf-neurips":           "https://blog.neurips.cc/feed/",
    "conf-iclr":              "https://blog.iclr.cc/feed/",
    "conf-acl":               "https://2025.aclweb.org/feed.xml",
    # Products (V4)
    "producthunt-ai":         "https://www.producthunt.com/feed?category=artificial-intelligence",
}


def _register_linkedin_company_feeds() -> None:
    """Public LinkedIn company pages via RSSHub (V6) — a ToS-safe bridge that
    reads only public company posts, never private content or LinkedIn's API.
    Built from the configurable RSSHub base so a self-hosted instance can
    replace the public one for reliability."""
    from app.core.config import settings

    base = settings.rsshub_base.rstrip("/")
    companies = {
        "linkedin-openai":      "openai",
        "linkedin-anthropic":   "anthropicresearch",
        "linkedin-deepmind":    "googledeepmind",
        "linkedin-huggingface": "huggingface",
        "linkedin-mistral":     "mistralai",
    }
    for source_id, slug in companies.items():
        RSS_SOURCES.setdefault(source_id, f"{base}/linkedin/company/{slug}")


_register_linkedin_company_feeds()


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

            # LinkedIn (RSSHub) and similar feeds put the whole post in the title;
            # condense it to a real headline so the card stays scannable.
            raw_title = entry.get("title", "")
            title = (
                _concise_title(raw_title, summary)
                if self.source_id.startswith("linkedin") or len(_strip_html(raw_title)) > 110
                else _strip_html(raw_title).strip()
            )

            items.append({
                "title": title,
                "url": link,
                "author": entry.get("author"),
                "summary": summary,
                "published_at": published,
                "trending_score": 0.0,
                "image_url": _rss_image(entry),
            })

        log.info("rss_fetched", source_id=self.source_id, count=len(items))
        return FetchResult(source_id=self.source_id, items=items)
