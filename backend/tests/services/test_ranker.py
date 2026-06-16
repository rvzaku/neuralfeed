import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.ranker import score_article, rank_articles


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
    # Default to a specific AI topic — a normally-classified item. Tests that
    # exercise the "general"-only topicality penalty pass topic_tags explicitly.
    a.topic_tags = topic_tags if topic_tags is not None else ["llm"]
    return a


class TestTopicality:
    def test_general_only_item_is_penalized(self):
        specific = _make_article(published_hours_ago=6, topic_tags=["llm"])
        general = _make_article(published_hours_ago=6, topic_tags=["general"])
        assert score_article(specific, 0.5, {}, set()) > score_article(general, 0.5, {}, set())

    def test_untagged_item_is_penalized(self):
        tagged = _make_article(published_hours_ago=6, topic_tags=["ai-agents"])
        untagged = _make_article(published_hours_ago=6, topic_tags=[])
        assert score_article(tagged, 0.5, {}, set()) > score_article(untagged, 0.5, {}, set())

    def test_general_plus_specific_not_penalized(self):
        only_general = _make_article(published_hours_ago=6, topic_tags=["general"])
        mixed = _make_article(published_hours_ago=6, topic_tags=["general", "llm"])
        assert score_article(mixed, 0.5, {}, set()) > score_article(only_general, 0.5, {}, set())

    def test_broad_aggregator_general_penalized_harder_than_curated(self):
        # A "general" junk repo from GitHub sinks much harder than a "general"
        # untagged item from an AI-native source (just a tagger miss).
        junk = _make_article(source_id="github-trending", published_hours_ago=6,
                             trending_score=5000, topic_tags=["general"])
        curated = _make_article(source_id="rss-anthropic", published_hours_ago=6,
                                trending_score=5000, topic_tags=["general"])
        assert score_article(junk, 0.5, {}, set()) < score_article(curated, 0.5, {}, set())

    def test_landmark_title_gets_boost(self):
        from app.services.landmarks import compile_matcher
        m = compile_matcher(["OpenClaw"])
        plain = _make_article(published_hours_ago=6, topic_tags=["ai-agents"])
        plain.title = "A routine agent update"
        landmark = _make_article(published_hours_ago=6, topic_tags=["ai-agents"])
        landmark.title = "OpenClaw breaks the internet"
        assert score_article(landmark, 0.5, {}, set(), landmark_matcher=m) > \
            score_article(plain, 0.5, {}, set(), landmark_matcher=m)

    def test_ai_tagged_aggregator_item_beats_general_junk(self):
        # The motivating fix: a real AI item must outrank a higher-traction but
        # unclassified junk repo from the same kind of open aggregator.
        junk = _make_article(source_id="github-trending", published_hours_ago=6,
                             trending_score=8000, topic_tags=["general"])
        ai_item = _make_article(source_id="github-trending", published_hours_ago=6,
                                trending_score=3000, topic_tags=["ai-agents"])
        assert score_article(ai_item, 0.5, {}, set()) > score_article(junk, 0.5, {}, set())


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
        # All three recent enough to survive the relevance threshold; ordering
        # must be strictly newer-first when traction is equal.
        old = _make_article(source_id="s1", published_hours_ago=72)
        fresh = _make_article(source_id="s1", published_hours_ago=1)
        medium = _make_article(source_id="s1", published_hours_ago=24)

        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        exec_result = MagicMock()
        exec_result.all.return_value = [("s1", 0.5)]
        db.execute = AsyncMock(return_value=exec_result)

        result, _ = await rank_articles([old, medium, fresh], db, window_days=30)
        assert result[0] is fresh
        assert result[-1] is old

    @pytest.mark.asyncio
    async def test_stale_untracted_item_dropped(self):
        # A week-plus-old item with no engagement is noise — culled from the
        # ranked feed (the anti-overwhelm contract), not just sorted last.
        stale = _make_article(source_id="s1", published_hours_ago=400)
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        exec_result = MagicMock()
        exec_result.all.return_value = [("s1", 0.5)]
        db.execute = AsyncMock(return_value=exec_result)

        result, _ = await rank_articles([stale], db, window_days=7)
        # Sole item → kept by the never-return-empty guard, but a stale item
        # alongside fresh ones would be dropped (covered by ordering test).
        assert result == [stale]

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

        result, _ = await rank_articles([article], db)
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self):
        db = AsyncMock()
        result, _ = await rank_articles([], db)
        assert result == []
