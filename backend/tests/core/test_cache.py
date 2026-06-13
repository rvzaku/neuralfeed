"""Feed cache must degrade to a silent no-op whenever Redis is unavailable or
disabled, never raising into the request path."""

import pytest

from app.core import cache


@pytest.fixture(autouse=True)
def _reset_cache_state(monkeypatch):
    # The module latches a global client/disabled flag; reset between tests.
    monkeypatch.setattr(cache, "_client", None)
    monkeypatch.setattr(cache, "_disabled", False)


async def test_disabled_returns_none_and_noops(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "feed_cache_enabled", False)

    assert await cache.get_json("k") is None
    await cache.set_json("k", {"a": 1}, 10)  # must not raise


async def test_connection_failure_disables_and_returns_none(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "feed_cache_enabled", True)

    class _Boom:
        async def get(self, *a, **k):
            raise ConnectionError("no redis")

        async def set(self, *a, **k):
            raise ConnectionError("no redis")

    monkeypatch.setattr(cache, "_get_client", lambda: _Boom())

    assert await cache.get_json("k") is None
    # The failure should have latched the cache off for the process.
    assert cache._disabled is True


async def test_roundtrip_with_fake_client(monkeypatch):
    store: dict = {}

    class _Fake:
        async def get(self, key):
            return store.get(key)

        async def set(self, key, value, ex=None):
            store[key] = value

    monkeypatch.setattr(cache, "_get_client", lambda: _Fake())

    await cache.set_json("k", {"ids": [1, 2], "total": 2}, 30)
    assert await cache.get_json("k") == {"ids": [1, 2], "total": 2}
