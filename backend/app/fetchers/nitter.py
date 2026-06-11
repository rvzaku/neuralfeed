"""
Twitter/X via Nitter RSS fallback.
Account list is loaded from the watched_accounts DB table (platform='twitter').
Falls back to a hardcoded seed list if the DB is unavailable.
"""
from typing import Optional
import feedparser
import httpx
import structlog
from app.fetchers.base import BaseFetcher, FetchResult
from app.fetchers.rss import _strip_html

log = structlog.get_logger()

NITTER_INSTANCES = [
    "https://nitter.net",          # alive as of 2026-06-11
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]

# Fallback used only when DB is not available (e.g. during tests)
_FALLBACK_ACCOUNTS = [
    "karpathy", "sama", "ylecun", "AnthropicAI",
    "OpenAI", "GoogleDeepMind", "huggingface", "swyx",
]


async def _load_accounts_from_db() -> list[str]:
    """Return enabled Twitter handles from watched_accounts table."""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.watched_account import WatchedAccount
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WatchedAccount.handle).where(
                    WatchedAccount.platform == "twitter",
                    WatchedAccount.enabled == True,
                )
            )
            handles = [row[0] for row in result.all()]
            return handles if handles else _FALLBACK_ACCOUNTS
    except Exception as e:
        log.warning("nitter_db_load_error", error=str(e))
        return _FALLBACK_ACCOUNTS


class NitterFetcher(BaseFetcher):
    source_id = "twitter-nitter"

    def __init__(self, accounts: Optional[list] = None):
        # If accounts passed explicitly (e.g. tests), use them; otherwise load from DB at fetch time
        self._explicit_accounts = accounts

    async def _try_fetch(self, client: httpx.AsyncClient, instance: str, account: str) -> list:
        url = f"{instance}/{account}/rss"
        try:
            # nitter.net serves an empty 200 body to clients without a browser UA
            resp = await client.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
            })
            if resp.status_code != 200 or not resp.text:
                return []
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:5]:
                link = entry.get("link", "")
                if not link:
                    continue
                items.append({
                    "title": _strip_html(entry.get("title", ""))[:200],
                    "url": link,
                    "author": f"@{account}",
                    "summary": _strip_html(entry.get("summary", ""))[:500] or None,
                    "published_at": entry.get("published"),
                    "trending_score": 0.0,
                })
            return items
        except Exception:
            return []

    async def fetch(self) -> FetchResult:
        accounts = self._explicit_accounts or await _load_accounts_from_db()
        all_items: list = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for account in accounts:
                for instance in NITTER_INSTANCES:
                    items = await self._try_fetch(client, instance, account)
                    if items:
                        all_items.extend(items)
                        break

        log.info("nitter_fetched", count=len(all_items))
        return FetchResult(source_id=self.source_id, items=all_items)
