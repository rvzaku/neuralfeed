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
