"""Guest mode: read-only, quota-protected public demo access."""

import pytest

from app.core.config import settings
from app.core.time import utcnow
from app.models.article import Article
from app.services import auth_service


@pytest.fixture
def guest_mode(monkeypatch):
    monkeypatch.setattr(settings, "guest_mode_enabled", True)
    monkeypatch.setattr(settings, "guest_summaries_enabled", False)


def _guest_headers() -> dict:
    return {"Authorization": f"Bearer {auth_service.create_guest_token()}"}


async def _seed_article(db, key, *, summary=None) -> Article:
    art = Article(
        id=f"guest-art-{key}",
        title="A Test Article",
        url=f"https://example.com/post-{key}",
        source_id="rss-openai",
        summary="snippet",
        ai_summary=summary,
        published_at=utcnow(),
        fetched_at=utcnow(),
    )
    db.add(art)
    await db.commit()
    return art


async def test_guest_token_issued_only_when_enabled(client, guest_mode):
    resp = await client.post("/api/v1/auth/guest")
    assert resp.status_code == 200
    assert auth_service.is_guest_token(resp.json()["access_token"])


async def test_guest_endpoint_hidden_when_disabled(client):
    # guest_mode_enabled defaults to False
    resp = await client.post("/api/v1/auth/guest")
    assert resp.status_code == 404


async def test_guest_cannot_write(client, guest_mode, db):
    await _seed_article(db, "bm")
    # Any mutating request with a guest token is blocked by middleware.
    resp = await client.post(
        "/api/v1/articles/guest-art-bm/bookmark", headers=_guest_headers()
    )
    assert resp.status_code == 403
    assert "read-only" in resp.json()["detail"].lower()


async def test_guest_summary_returns_cache_without_generating(client, guest_mode, db):
    await _seed_article(db, "cache", summary="## What it is\n\nA structured cached brief about the thing.")
    resp = await client.get(
        "/api/v1/articles/guest-art-cache/summary", headers=_guest_headers()
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["cached"] is True
    assert "What it is" in body["markdown"]


async def test_guest_summary_blocked_on_cache_miss(client, guest_mode, db):
    # No cached summary + guest_summaries_enabled is False → never calls the LLM.
    await _seed_article(db, "miss", summary=None)
    resp = await client.get(
        "/api/v1/articles/guest-art-miss/summary", headers=_guest_headers()
    )
    assert resp.status_code == 503
    assert "sign in" in resp.json()["detail"].lower()


_ORIGIN = "https://neuralfeed.vercel.app"


async def test_guest_preflight_not_rate_limited_and_has_cors(client, guest_mode, monkeypatch):
    # Regression: CORS preflight (OPTIONS) for the guest endpoint must never be
    # rate-limited and must echo CORS headers — otherwise the browser blocks the
    # real POST. Hammer it well past the auth budget to prove it's exempt.
    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 3)
    for _ in range(10):
        resp = await client.options(
            "/api/v1/auth/guest",
            headers={
                "Origin": _ORIGIN,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == _ORIGIN


async def test_rate_limited_response_carries_cors_headers(client, guest_mode, monkeypatch):
    # Regression: a 429 is produced by the rate-limit middleware, which sits
    # INSIDE the CORS middleware — so the error response must still carry the
    # Access-Control-Allow-Origin header, or the browser shows an opaque failure.
    # (conftest disables rate limiting by default — turn it back on here.)
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 2)
    statuses = []
    for _ in range(5):
        resp = await client.post("/api/v1/auth/guest", headers={"Origin": _ORIGIN})
        statuses.append(resp.status_code)
        assert resp.headers["access-control-allow-origin"] == _ORIGIN
    assert 429 in statuses  # budget exhausted within the window
