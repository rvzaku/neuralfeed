"""Per-user article state: authed users get their own read/bookmark/feedback
overlay while anonymous requests keep mutating the legacy global columns."""

import pytest

from app.core.time import utcnow
from app.models.article import Article

pytestmark = pytest.mark.asyncio


async def _make_article(db, aid="ustate-a1"):
    art = Article(
        id=aid, title="Test article", url=f"https://example.com/{aid}",
        source_id="rss-openai", published_at=utcnow(), fetched_at=utcnow(),
        topic_tags=[], is_read=False, is_bookmarked=False,
        feedback=None, trending_score=0.0,
    )
    db.add(art)
    await db.commit()
    return art


async def _register(client, email):
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_bookmark_is_per_user(client, db):
    art = await _make_article(db, "ustate-bm")
    h1 = await _register(client, "u1@example.com")
    h2 = await _register(client, "u2@example.com")

    resp = await client.post(f"/api/v1/articles/{art.id}/bookmark", headers=h1)
    assert resp.status_code == 200
    assert resp.json()["is_bookmarked"] is True

    # Other user unaffected; global column untouched
    resp = await client.post(f"/api/v1/articles/{art.id}/bookmark", headers=h2)
    assert resp.json()["is_bookmarked"] is True  # their own first toggle
    await db.refresh(art)
    assert art.is_bookmarked is False


async def test_feedback_overlay_in_feed(client, db):
    art = await _make_article(db, "ustate-fb")
    h1 = await _register(client, "u3@example.com")

    resp = await client.post(
        "/api/v1/feedback", json={"article_id": art.id, "value": 1}, headers=h1
    )
    assert resp.status_code == 200
    assert resp.json()["feedback"] == 1

    feed = await client.get("/api/v1/feed?limit=100&ranked=false", headers=h1)
    item = next(i for i in feed.json()["items"] if i["id"] == art.id)
    assert item["feedback"] == 1

    # Anonymous view shows global state, not the user's
    feed_anon = await client.get("/api/v1/feed?limit=100&ranked=false")
    item_anon = next(i for i in feed_anon.json()["items"] if i["id"] == art.id)
    assert item_anon["feedback"] == 1 or item_anon["feedback"] is None


async def test_preferences_are_namespaced(client, db):
    h1 = await _register(client, "u4@example.com")

    await client.put(
        "/api/v1/preferences/topic_weights", json={"value": '{"llm": 1.0}'}, headers=h1
    )
    mine = await client.get("/api/v1/preferences", headers=h1)
    assert mine.json().get("topic_weights") == {"llm": 1.0}

    anon = await client.get("/api/v1/preferences")
    assert "topic_weights" not in anon.json() or anon.json() != mine.json()
