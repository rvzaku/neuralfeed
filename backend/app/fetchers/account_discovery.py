"""
Account discovery fetcher.

Reads docs/curated_accounts.json (local) and optional remote lists to populate
the watched_accounts table. Nitter/LinkedIn fetchers then query that table
instead of using a hardcoded list.
"""
import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watched_account import WatchedAccount

log = structlog.get_logger()

# Resolve path relative to the repo root (backend/../docs/)
_REPO_ROOT = Path(__file__).resolve().parents[3]
CURATED_JSON = _REPO_ROOT / "docs" / "curated_accounts.json"


def _account_id(platform: str, handle: str) -> str:
    return f"{platform}:{handle.lstrip('@').lower()}"


def _parse_account(entry: dict, source: str) -> Optional[dict]:
    platform = entry.get("platform", "").lower()
    handle   = entry.get("handle", "").strip().lstrip("@")
    name     = entry.get("display_name") or handle
    if not platform or not handle:
        return None
    return {
        "id": _account_id(platform, handle),
        "platform": platform,
        "handle": handle,
        "display_name": name,
        "source_of_discovery": entry.get("source_of_discovery") or source,
        "notes": entry.get("notes"),
    }


async def _fetch_remote_list(url: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data.get("accounts", []) if isinstance(data, dict) else []
    except Exception as e:
        log.warning("account_discovery_remote_error", url=url, error=str(e))
        return []


async def discover_accounts(db: AsyncSession) -> int:
    """Read local + remote curated lists and upsert into watched_accounts. Returns upserted count."""
    raw_accounts: list[dict] = []

    # --- Local curated list ---
    if CURATED_JSON.exists():
        try:
            data = json.loads(CURATED_JSON.read_text())
            raw_accounts.extend(data.get("accounts", []))

            # Optional remote lists (skipped gracefully if unreachable)
            for feed in data.get("discovery_feeds", []):
                url = feed.get("url", "")
                if url:
                    remote = await _fetch_remote_list(url)
                    raw_accounts.extend(remote)
        except Exception as e:
            log.warning("account_discovery_local_error", error=str(e))

    upserted = 0
    today = date.today()
    for raw in raw_accounts:
        parsed = _parse_account(raw, source="curated_accounts.json")
        if not parsed:
            continue
        existing = await db.get(WatchedAccount, parsed["id"])
        if existing is None:
            db.add(WatchedAccount(
                **parsed,
                enabled=True,
                added_on=today,
            ))
            upserted += 1
        # Don't overwrite enabled/notes on existing accounts — user may have changed them

    if upserted:
        await db.commit()

    log.info("account_discovery_complete", upserted=upserted, total=len(raw_accounts))
    return upserted
