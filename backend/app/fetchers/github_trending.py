import asyncio
import re
from datetime import datetime, timedelta, timezone

import httpx
import structlog
from app.core.config import settings
from app.fetchers.base import BaseFetcher, FetchResult

log = structlog.get_logger()

# One trending <article class="Box-row"> block per repo
_ARTICLE_RE = re.compile(r'<article class="Box-row"[^>]*>(.*?)</article>', re.DOTALL)
# lh-condensed may sit on the <h2> or on the <a> depending on page version
_REPO_RE = re.compile(r'<h2[^>]*>\s*<a[^>]*href="/([^/"]+)/([^/"]+)"', re.DOTALL)
_DESC_RE = re.compile(r'<p class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', re.DOTALL)
_STARS_RE = re.compile(r'href="/[^"]+/stargazers"[^>]*>(.*?)</a>', re.DOTALL)
_TODAY_RE = re.compile(r'([\d,]+)\s+stars\s+(?:today|this\s+week|this\s+month)')
_TAG_RE = re.compile(r"<[^>]+>")


def _to_int(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


def _clean(html: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", html)).strip()


def _gh_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "NeuralFeed/0.1"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def parse_trending(html: str) -> list[dict]:
    """Extract owner/repo, description, total stars, and stars-today from the
    trending page. Regex over article blocks — the page is server-rendered
    and structurally stable."""
    repos = []
    for block in _ARTICLE_RE.findall(html):
        repo_m = _REPO_RE.search(block)
        if not repo_m:
            continue
        owner, repo = repo_m.group(1).strip(), repo_m.group(2).strip()
        desc_m = _DESC_RE.search(block)
        stars_m = _STARS_RE.search(block)
        today_m = _TODAY_RE.search(block)
        repos.append({
            "owner": owner,
            "repo": repo,
            "url": f"https://github.com/{owner}/{repo}",
            "description": _clean(desc_m.group(1)) if desc_m else None,
            "stars_total": _to_int(stars_m.group(1)) if stars_m else 0,
            "stars_today": _to_int(today_m.group(1)) if today_m else 0,
        })
    return repos


class GithubTrendingFetcher(BaseFetcher):
    source_id = "github-trending"

    async def _repo_meta(self, client: httpx.AsyncClient, owner: str, repo: str) -> dict:
        """The trending page has no dates and its scraped star counts are
        unreliable (HTML drift). The repo API gives the authoritative
        created_at and live stargazers_count — the numbers the feed shows."""
        try:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}", headers=_gh_headers()
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "created_at": data.get("created_at"),
                    "stars_total": int(data.get("stargazers_count", 0)),
                    "forks": int(data.get("forks_count", 0)),
                    "topics": data.get("topics") or [],
                    "language": data.get("language"),
                }
        except Exception as e:
            log.debug("github_repo_meta_failed", owner=owner, repo=repo, error=str(e))
        return {}

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

        repos = parse_trending(resp.text)
        now = datetime.now(timezone.utc).isoformat()

        items = []
        async with httpx.AsyncClient(timeout=15) as client:
            for r in repos:
                meta = await self._repo_meta(client, r["owner"], r["repo"])
                # Authoritative API star count; fall back to the scrape only if
                # the API call failed (rate limit / network).
                stars_total = meta.get("stars_total") or r["stars_total"]
                items.append({
                    "title": f"{r['owner']}/{r['repo']}",
                    "url": r["url"],
                    "author": r["owner"],
                    "summary": r["description"] or None,
                    "published_at": meta.get("created_at") or now,
                    "trending_score": float(r["stars_today"] or stars_total),
                    "engagement": {
                        "stars_total": stars_total,
                        "stars_today": r["stars_today"],
                        "forks": meta.get("forks", 0),
                    },
                })

        log.info("github_trending_fetched", count=len(items))
        return FetchResult(source_id=self.source_id, items=items)

    async def backfill(self, days: int = 30) -> FetchResult:
        """Top new/active AI repos over a window via the Search API — the
        trending page only knows about today."""
        return await _search_repos(self.source_id, self._backfill_queries(days), days)

    @staticmethod
    def _backfill_queries(days: int) -> list[str]:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        return [
            f"created:>{since} topic:llm",
            f"created:>{since} topic:machine-learning",
            f"created:>{since} language:python topic:ai",
        ]


class GithubTopicFetcher(BaseFetcher):
    """V8 user-added source: track one GitHub topic or org via the Search API."""

    def __init__(self, source_id: str, value: str):
        self.source_id = source_id
        self.value = value.strip()

    def _queries(self, days: int) -> list[str]:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        # The value may be a topic or an org — query both; the wrong one
        # just returns zero results and costs one cheap search call
        return [f"pushed:>{since} topic:{self.value}", f"pushed:>{since} org:{self.value}"]

    async def fetch(self) -> FetchResult:
        return await _search_repos(self.source_id, self._queries(7), 7)

    async def backfill(self, days: int = 30) -> FetchResult:
        return await _search_repos(self.source_id, self._queries(days), days)


async def _search_repos(source_id: str, queries: list[str], days: int) -> FetchResult:
    items, seen = [], set()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            for q in queries:
                resp = await client.get(
                    "https://api.github.com/search/repositories",
                    params={"q": q, "sort": "stars", "order": "desc", "per_page": 50},
                    headers=_gh_headers(),
                )
                if resp.status_code != 200:
                    log.warning("github_search_failed", status=resp.status_code, q=q)
                    continue
                for r in resp.json().get("items", []):
                    if r["html_url"] in seen:
                        continue
                    seen.add(r["html_url"])
                    items.append({
                        "title": r["full_name"],
                        "url": r["html_url"],
                        "author": r["owner"]["login"],
                        "summary": r.get("description") or None,
                        "published_at": r.get("created_at"),
                        "trending_score": float(r.get("stargazers_count", 0)),
                        "engagement": {
                            "stars_total": int(r.get("stargazers_count", 0)),
                            "forks": int(r.get("forks_count", 0)),
                        },
                    })
                await asyncio.sleep(2)  # search API: 10 req/min unauthenticated
    except Exception as e:
        if not items:
            return FetchResult(source_id=source_id, error=str(e))

    log.info("github_search_fetched", source_id=source_id, count=len(items), window_days=days)
    return FetchResult(source_id=source_id, items=items)
