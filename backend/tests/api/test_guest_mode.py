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
