"""Daily digest: in-app endpoint returns the ranked top stories, and the email
renderer + send path degrade safely when email is unconfigured."""

import pytest

from app.core.time import utcnow
from app.models.article import Article

pytestmark = pytest.mark.asyncio


async def _seed(db, n=8, prefix="dig"):
    now = utcnow()
    for i in range(n):
        db.add(Article(
            id=f"{prefix}-{i:03d}", title=f"Digest story {i}",
            url=f"https://example.com/{prefix}/{i}", source_id="rss-openai",
            summary=f"Summary for story {i}.", published_at=now, fetched_at=now,
            topic_tags=["llm"], is_read=False, is_bookmarked=False,
            feedback=None, trending_score=float(i),
        ))
    await db.commit()


async def test_digest_endpoint_returns_top_stories(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/digest?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 5
    assert len(data["items"]) == 5
    first = data["items"][0]
    assert first["title"] and first["url"]
    assert first["source_name"]  # resolved from the Source registry
    assert "blurb" in first


async def test_digest_endpoint_respects_limit(client, db):
    await _seed(db, n=6, prefix="digcap")
    resp = await client.get("/api/v1/digest?limit=3")
    assert resp.status_code == 200
    assert resp.json()["count"] == 3  # limit honored

    # Out-of-range limit is rejected by validation (le=10).
    too_big = await client.get("/api/v1/digest?limit=99")
    assert too_big.status_code == 422


async def test_render_digest_email_is_safe_html():
    from app.services.email import render_digest_email

    digest = {
        "count": 1,
        "items": [{
            "title": "<script>alert(1)</script> Model drop",
            "url": "https://example.com/x",
            "source_name": "OpenAI",
            "blurb": "A & B < C",
        }],
    }
    html = render_digest_email(digest)
    assert "<script>alert(1)</script>" not in html  # escaped
    assert "Model drop" in html
    assert "OpenAI" in html


async def test_send_email_noops_without_key(monkeypatch):
    from app.core.config import settings
    from app.services.email import send_email

    monkeypatch.setattr(settings, "resend_api_key", "")
    assert await send_email("a@b.com", "subj", "<p>hi</p>") is False
