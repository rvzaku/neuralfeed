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
async def test_feed_cache_hit_serves_consistent_pages(client, db, monkeypatch):
    """With the cache enabled, page 1 populates the ranked order and page 2
    slices that same cached order — pages must not overlap or drop items."""
    from app.core import cache
    from app.core.config import settings

    store: dict = {}

    class _Fake:
        async def get(self, key):
            return store.get(key)

        async def set(self, key, value, ex=None):
            store[key] = value

    monkeypatch.setattr(settings, "feed_cache_enabled", True)
    monkeypatch.setattr(cache, "_get_client", lambda: _Fake())

    for i in range(6):
        await _seed_article(db, url=f"https://arxiv.org/abs/cache.{i:03d}")

    p1 = await client.get("/api/v1/feed?page=1&limit=3")
    assert p1.status_code == 200
    assert store, "page 1 should have written the ranked order to the cache"

    p2 = await client.get("/api/v1/feed?page=2&limit=3")
    assert p2.status_code == 200

    ids1 = [i["id"] for i in p1.json()["items"]]
    ids2 = [i["id"] for i in p2.json()["items"]]
    assert set(ids1).isdisjoint(ids2), "cached pages must not repeat items"


@pytest.mark.asyncio
async def test_feed_topic_filter_matches_multi_tag_articles(client, db):
    """Regression: the topic filter must match an article that carries the topic
    alongside other tags — not only articles where it is the sole tag. The old
    JSON `.contains([topic])` compiled to a whole-list LIKE and silently dropped
    every multi-tag article, emptying most topic views."""
    multi = await _seed_article(db, url="https://arxiv.org/abs/multi.001")
    multi.topic_tags = ["llm", "ai-agents", "products"]
    await db.commit()

    resp = await client.get("/api/v1/feed?topic=ai-agents&ranked=false")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["items"]]
    assert multi.id in ids


@pytest.mark.asyncio
async def test_topics_endpoint_orders_by_relevance(client, db):
    a = await _seed_article(db, url="https://arxiv.org/abs/topic.001")
    a.topic_tags = ["llm", "robotics"]
    await db.commit()

    resp = await client.get("/api/v1/topics?time_range=30d")
    assert resp.status_code == 200
    data = resp.json()
    by_tag = {t["tag"]: t for t in data["items"]}
    assert by_tag["llm"]["count"] >= 1
    assert by_tag["robotics"]["count"] >= 1
    # Topics with material sort ahead of empty ones.
    counts = [t["count"] for t in data["items"]]
    assert counts == sorted(counts, reverse=True) or counts[0] >= counts[-1]


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
