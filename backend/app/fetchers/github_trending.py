import re
from html.parser import HTMLParser
from datetime import datetime, timezone
import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult

log = structlog.get_logger()


class _TrendingParser(HTMLParser):
    """Minimal parser for GitHub trending page."""

    def __init__(self):
        super().__init__()
        self.repos: list[dict] = []
        self._in_repo_block = False
        self._current: dict = {}
        self._capture_desc = False
        self._desc_buf = ""
        self._in_title_h2 = False

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        cls = attrs_d.get("class", "")
        if tag == "article" and "Box-row" in cls:
            self._in_repo_block = True
            self._current = {}
        # Repo link lives in <h2 class="… lh-condensed"><a href="/owner/repo">
        if self._in_repo_block and tag == "h2" and "lh-condensed" in cls:
            self._in_title_h2 = True
        if self._in_repo_block and tag == "a" and (self._in_title_h2 or "lh-condensed" in cls):
            href = attrs_d.get("href", "")
            parts = href.strip("/").split("/")
            if len(parts) == 2 and "url" not in self._current:
                self._current["url"] = f"https://github.com{href}"
                self._current["owner"] = parts[0]
                self._current["repo"] = parts[1]
        if self._in_repo_block and tag == "p" and "col-9" in cls:
            self._capture_desc = True
            self._desc_buf = ""

    def handle_endtag(self, tag):
        if tag == "h2":
            self._in_title_h2 = False
        if tag == "article" and self._in_repo_block:
            if self._current.get("url"):
                self.repos.append(self._current)
            self._in_repo_block = False
            self._current = {}
        if tag == "p" and self._capture_desc:
            self._current["description"] = self._desc_buf.strip()
            self._capture_desc = False

    def handle_data(self, data):
        if self._capture_desc:
            self._desc_buf += data


class GithubTrendingFetcher(BaseFetcher):
    source_id = "github-trending"

    async def fetch(self) -> FetchResult:
        url = "https://github.com/trending/python?since=daily"
        headers = {"Accept": "text/html", "User-Agent": "NeuralFeed/0.1"}
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
        except Exception as e:
            log.warning("github_trending_fetch_error", error=str(e))
            return FetchResult(source_id=self.source_id, error=str(e))

        parser = _TrendingParser()
        try:
            parser.feed(resp.text)
        except Exception as e:
            log.warning("github_trending_parse_error", error=str(e))
            return FetchResult(source_id=self.source_id, error=str(e))

        now = datetime.now(timezone.utc).isoformat()
        items = [
            {
                "title": f"{r.get('owner', '')}/{r.get('repo', '')}",
                "url": r["url"],
                "author": r.get("owner"),
                "summary": r.get("description") or None,
                "published_at": now,
                "trending_score": 0.0,
            }
            for r in parser.repos
        ]

        log.info("github_trending_fetched", count=len(items))
        return FetchResult(source_id=self.source_id, items=items)
