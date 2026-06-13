"""Tiny async JSON cache backed by Redis, with a hard graceful fallback.

The feed's ranked ordering is expensive to compute (load ~2000 rows → per-day
caps → cross-source dedupe → personalized rank → interleave) yet identical
across the pages of one infinite-scroll session. Caching the ordered id list
for a short TTL turns page 2..N from "redo all that work" into "slice a list +
load 20 rows by id".

Redis was retired at runtime in favor of APScheduler, so it may be absent in a
deploy. Every operation therefore degrades to a no-op on any connection error,
and after the first failure the client is latched off for the process lifetime
so we never pay the connect timeout twice. Net effect: with Redis the feed is
cached; without it the feed simply recomputes — never errors.
"""

import json
from typing import Any, Optional

import structlog

from app.core.config import settings

log = structlog.get_logger()

_client: Any = None
_disabled = False


def _get_client():
    global _client, _disabled
    if _disabled or not settings.feed_cache_enabled:
        return None
    if _client is None:
        try:
            import redis.asyncio as aioredis

            _client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
        except Exception as e:  # missing lib / bad URL → disable for good
            log.warning("cache_init_failed", error=str(e))
            _disabled = True
            return None
    return _client


def _disable(reason: str, error: str) -> None:
    """Latch the cache off after the first connection failure."""
    global _disabled
    _disabled = True
    log.info("cache_disabled", reason=reason, error=error)


async def get_json(key: str) -> Optional[Any]:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        _disable("get_failed", str(e))
        return None


async def set_json(key: str, value: Any, ttl: int) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        await client.set(key, json.dumps(value, separators=(",", ":")), ex=ttl)
    except Exception as e:
        _disable("set_failed", str(e))
