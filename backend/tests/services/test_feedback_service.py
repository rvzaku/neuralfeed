"""feedback_service: feedback persists, signal_score recomputes, topic weights adapt."""

import json

import pytest
from sqlalchemy import select

from app.core.time import utcnow
from app.models.article import Article, make_title_hash
from app.models.user_preference import UserPreference
from app.services.feedback_service import apply_feedback


@pytest.fixture(autouse=True)
async def _clean_weights(db):
    """The in-memory engine is session-scoped — reset weights between tests."""
    pref = await db.get(UserPreference, "topic_weights")
    if pref:
        await db.delete(pref)
        await db.commit()
    yield


async def _make_article(db, article_id=None, tags=None, source_id="arxiv-cs-ai"):
    import uuid
    article_id = article_id or f"fb-{uuid.uuid4().hex[:8]}"
    article = Article(
        id=article_id, title=f"Test {article_id}", url=f"https://x.test/{article_id}",
        source_id=source_id, author=None, summary="s",
        published_at=utcnow(), fetched_at=utcnow(),
        topic_tags=tags or ["llm", "general"], is_read=False, is_bookmarked=False,
        feedback=None, trending_score=0.0, title_hash=make_title_hash(f"Test {article_id}"),
    )
    db.add(article)
    await db.commit()
    return article


async def _weights(db) -> dict:
    pref = await db.get(UserPreference, "topic_weights")
    return json.loads(pref.value) if pref else {}


@pytest.mark.asyncio
async def test_thumbs_up_nudges_topic_weights_up(db):
    article = await _make_article(db, tags=["llm", "agents", "general"])
    await apply_feedback(article.id, 1, db)

    weights = await _weights(db)
    assert weights["llm"] == pytest.approx(0.1)
    assert weights["agents"] == pytest.approx(0.1)
    assert "general" not in weights  # catch-all tag never weighted
    assert article.feedback == 1


@pytest.mark.asyncio
async def test_thumbs_down_nudges_weights_down_and_clamps(db):
    article = await _make_article(db, tags=["cv"])
    db.add(UserPreference(key="topic_weights", value=json.dumps({"cv": -0.95})))
    await db.commit()

    await apply_feedback(article.id, -1, db)
    weights = await _weights(db)
    assert weights["cv"] == pytest.approx(-1.0)  # clamped at floor


@pytest.mark.asyncio
async def test_weight_ceiling_clamps(db):
    article = await _make_article(db, tags=["llm"])
    db.add(UserPreference(key="topic_weights", value=json.dumps({"llm": 1.95})))
    await db.commit()

    await apply_feedback(article.id, 1, db)
    weights = await _weights(db)
    assert weights["llm"] == pytest.approx(2.0)


@pytest.mark.asyncio
async def test_clearing_feedback_does_not_touch_weights(db):
    article = await _make_article(db, tags=["llm"])
    await apply_feedback(article.id, 0, db)
    assert article.feedback is None
    assert await _weights(db) == {}


@pytest.mark.asyncio
async def test_signal_score_recomputed(db):
    article = await _make_article(db, source_id="github-trending")  # isolated source
    await apply_feedback(article.id, 1, db)

    from app.models.source import Source
    source = await db.get(Source, "github-trending")
    assert source.signal_score == 1.0  # 1 positive / 1 rated
