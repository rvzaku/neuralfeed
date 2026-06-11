import pytest
from datetime import datetime, timezone
from app.services.ingest import ingest_items
from app.models.article import Article
from sqlalchemy import select


@pytest.mark.asyncio
async def test_ingest_inserts_items(db):
    items = [
        {"title": "Paper A", "url": "https://arxiv.org/abs/ingest.001", "summary": "Abstract A", "published_at": datetime.now(timezone.utc).isoformat(), "trending_score": 0.0},
        {"title": "Paper B", "url": "https://arxiv.org/abs/ingest.002", "summary": "Abstract B", "published_at": datetime.now(timezone.utc).isoformat(), "trending_score": 0.0},
    ]
    count = await ingest_items(items, "arxiv-cs-ai", db)
    assert count == 2


@pytest.mark.asyncio
async def test_ingest_dedup_by_url(db):
    items = [
        {"title": "Dup Paper", "url": "https://arxiv.org/abs/dedup.001", "summary": None, "published_at": None, "trending_score": 0.0},
    ]
    first = await ingest_items(items, "arxiv-cs-ai", db)
    second = await ingest_items(items, "arxiv-cs-ai", db)
    assert first == 1
    assert second == 0  # duplicate skipped


@pytest.mark.asyncio
async def test_ingest_skips_empty_url(db):
    items = [{"title": "No URL", "url": "", "summary": None, "published_at": None, "trending_score": 0.0}]
    count = await ingest_items(items, "arxiv-cs-ai", db)
    assert count == 0


@pytest.mark.asyncio
async def test_ingest_title_similarity_dedup_same_source(db):
    a = {"title": "The Qwen 3 Released", "url": "https://example.com/t1", "summary": None, "published_at": None, "trending_score": 0.0}
    b = {"title": "Qwen 3 released!",    "url": "https://example.com/t2", "summary": None, "published_at": None, "trending_score": 0.0}
    assert await ingest_items([a], "reddit-ml", db) == 1
    assert await ingest_items([b], "reddit-ml", db) == 0


@pytest.mark.asyncio
async def test_ingest_bad_date_falls_back_to_now(db):
    items = [{"title": "Bad date item", "url": "https://example.com/t3", "summary": None, "published_at": "not-a-date", "trending_score": 0.0}]
    assert await ingest_items(items, "reddit-ml", db) == 1
    art = (await db.execute(select(Article).where(Article.url == "https://example.com/t3"))).scalar_one()
    assert art.published_at is not None


@pytest.mark.asyncio
async def test_ingest_truncates_long_summary(db):
    items = [{"title": "Long summary item", "url": "https://example.com/t4", "summary": "x" * 900, "published_at": None, "trending_score": 0.0}]
    await ingest_items(items, "reddit-ml", db)
    art = (await db.execute(select(Article).where(Article.url == "https://example.com/t4"))).scalar_one()
    assert len(art.summary) <= 501  # 500 chars + ellipsis


@pytest.mark.asyncio
async def test_ingest_tags_topics_and_sets_title_hash(db):
    items = [{"title": "New LLM fine-tuning method for language models", "url": "https://example.com/t5", "summary": "transformer training", "published_at": None, "trending_score": 0.0}]
    await ingest_items(items, "arxiv-cs-ai", db)
    art = (await db.execute(select(Article).where(Article.url == "https://example.com/t5"))).scalar_one()
    assert art.title_hash
    assert isinstance(art.topic_tags, list)
