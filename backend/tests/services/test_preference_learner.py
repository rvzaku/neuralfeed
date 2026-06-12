import json

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.article import Article
from app.models.user_preference import UserPreference
from app.services.preference_learner import learn


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


def _article(tags=("llm", "ai-agents"), source_id="reddit-ml"):
    from datetime import datetime
    return Article(
        id="a1", title="t", url="https://x.test/1", source_id=source_id,
        published_at=datetime(2026, 6, 1), fetched_at=datetime(2026, 6, 1),
        topic_tags=list(tags), is_read=False, is_bookmarked=False,
        trending_score=0.0,
    )


async def _weights(db: AsyncSession, key="topic_weights") -> dict:
    pref = await db.get(UserPreference, key)
    return json.loads(pref.value) if pref else {}


@pytest.mark.asyncio
async def test_like_boosts_topics_and_source(db):
    await learn(db, None, _article(), "like")
    await db.commit()
    weights = await _weights(db)
    assert weights["llm"] == 0.15
    assert weights["ai-agents"] == 0.15
    affinity = await _weights(db, "source_affinity")
    assert affinity["reddit-ml"] == 0.15


@pytest.mark.asyncio
async def test_dislike_pushes_harder_than_like(db):
    await learn(db, None, _article(), "like")
    await learn(db, None, _article(), "dislike")
    await db.commit()
    weights = await _weights(db)
    assert weights["llm"] == -0.1  # 0.15 - 0.25


@pytest.mark.asyncio
async def test_toggling_like_off_reverses_learning(db):
    await learn(db, None, _article(), "like")
    await learn(db, None, _article(), "like", previous_feedback=1)  # toggle off
    await db.commit()
    assert await _weights(db) == {}  # zeroed entries are pruned


@pytest.mark.asyncio
async def test_weights_clamp_at_one(db):
    for _ in range(10):
        await learn(db, None, _article(), "bookmark")
    await db.commit()
    weights = await _weights(db)
    assert weights["llm"] == 1.0
