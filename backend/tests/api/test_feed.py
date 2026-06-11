import pytest
from datetime import datetime, timezone
from app.models.article import Article, make_article_id


async def _seed_article(db, source_id="arxiv-cs-ai", url="https://arxiv.org/abs/test.001"):
    now = datetime.now(timezone.utc)
    a = Article(
        id=make_article_id(source_id, url),
        title="Test Paper",
        url=url,
        source_id=source_id,
        summary="A test summary.",
        published_at=now,
        fetched_at=now,
        topic_tags=["llm"],
        is_read=False,
        is_bookmarked=False,
        feedback=None,
        trending_score=0.0,
    )
    db.add(a)
    await db.commit()
    return a


@pytest.mark.asyncio
async def test_feed_empty(client):
    resp = await client.get("/api/v1/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_feed_returns_article(client, db):
    a = await _seed_article(db)
    resp = await client.get("/api/v1/feed")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["items"]]
    assert a.id in ids


@pytest.mark.asyncio
async def test_feed_pagination(client, db):
    for i in range(5):
        await _seed_article(db, url=f"https://arxiv.org/abs/page.{i:03d}")
    resp = await client.get("/api/v1/feed?page=1&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 2
    assert data["has_more"] is True or data["total"] >= 1


@pytest.mark.asyncio
async def test_sources_list(client):
    resp = await client.get("/api/v1/sources")
    assert resp.status_code == 200
    sources = resp.json()
    assert len(sources) >= 11
    ids = [s["id"] for s in sources]
    assert "arxiv-cs-ai" in ids
    assert "reddit-ml" in ids
    assert "hf-models" in ids
    assert "youtube-ai" in ids


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
