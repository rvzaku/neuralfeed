import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.ranker import score_article, rank_articles, _recency_score


def _make_article(
    source_id="src-a",
    published_hours_ago=1,
    trending_score=0.0,
    feedback=None,
    topic_tags=None,
):
    a = MagicMock()
    a.source_id = source_id
    a.published_at = datetime.now(timezone.utc) - timedelta(hours=published_hours_ago)
    a.trending_score = trending_score
    a.feedback = feedback
    a.topic_tags = topic_tags or []
    return a


class TestRecencyScore:
    def test_fresh_article_scores_near_one(self):
        score = _recency_score(datetime.now(timezone.utc) - timedelta(minutes=30))
        assert score > 0.9

    def test_old_article_scores_near_zero(self):
        score = _recency_score(datetime.now(timezone.utc) - timedelta(days=30))
        assert score < 0.1


class TestScoreArticle:
    def test_new_high_signal_scores_high(self):
        article = _make_article(published_hours_ago=1)
        score = score_article(article, source_signal=0.9, topic_weights={}, muted_sources=set())
        assert score > 0.6

    def test_old_low_signal_scores_low(self):
        article = _make_article(published_hours_ago=24 * 30)
        score = score_article(article, source_signal=0.1, topic_weights={}, muted_sources=set())
        assert score < 0.15

    def test_muted_source_returns_negative(self):
        article = _make_article(source_id="bad-source")
        score = score_article(
            article, source_signal=0.9, topic_weights={}, muted_sources={"bad-source"}
        )
        assert score == -1.0

    def test_liked_feedback_boosts_score(self):
        base = _make_article(published_hours_ago=6)
        liked = _make_article(published_hours_ago=6, feedback=1)
        s_base = score_article(base, 0.5, {}, set())
        s_liked = score_article(liked, 0.5, {}, set())
        assert s_liked > s_base

    def test_disliked_feedback_reduces_score(self):
        base = _make_article(published_hours_ago=6)
        disliked = _make_article(published_hours_ago=6, feedback=-1)
        s_base = score_article(base, 0.5, {}, set())
        s_disliked = score_article(disliked, 0.5, {}, set())
        assert s_disliked < s_base

    def test_topic_boost_increases_score(self):
        no_boost = _make_article(topic_tags=[])
        boosted = _make_article(topic_tags=["llm"])
        s_no = score_article(no_boost, 0.5, {"llm": 0.8}, set())
        s_boost = score_article(boosted, 0.5, {"llm": 0.8}, set())
        assert s_boost > s_no


class TestRankArticles:
    @pytest.mark.asyncio
    async def test_orders_by_score_descending(self):
        old = _make_article(source_id="s1", published_hours_ago=200)
        fresh = _make_article(source_id="s1", published_hours_ago=1)
        medium = _make_article(source_id="s1", published_hours_ago=48)

        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        exec_result = MagicMock()
        exec_result.all.return_value = [("s1", 0.5)]
        db.execute = AsyncMock(return_value=exec_result)

        result = await rank_articles([old, medium, fresh], db)
        assert result[0] is fresh
        assert result[-1] is old

    @pytest.mark.asyncio
    async def test_muted_source_excluded(self):
        article = _make_article(source_id="muted-src")

        pref_mock = MagicMock()
        pref_mock.value = json.dumps(["muted-src"])

        async def fake_get(model, key):
            if key == "muted_sources":
                return pref_mock
            return None

        db = AsyncMock()
        db.get = AsyncMock(side_effect=fake_get)
        exec_result = MagicMock()
        exec_result.all.return_value = [("muted-src", 0.5)]
        db.execute = AsyncMock(return_value=exec_result)

        result = await rank_articles([article], db)
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self):
        db = AsyncMock()
        result = await rank_articles([], db)
        assert result == []
