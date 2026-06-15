"""V6 Hotness Index: cross-source velocity → colour band."""

import json
from datetime import timedelta
from unittest.mock import MagicMock

from app.core.time import utcnow
from app.services.hotness import heat_level, hotness, topic_heat


def _article(aid, source_id, published_ago_h=2, trending_score=0.0,
             engagement=None, topic_tags=None):
    a = MagicMock()
    a.id = aid
    a.source_id = source_id
    a.published_at = utcnow() - timedelta(hours=published_ago_h)
    a.trending_score = trending_score
    a.engagement = json.dumps(engagement) if engagement else None
    a.topic_tags = topic_tags or []
    return a


class TestHotness:
    def test_fresh_multi_source_story_is_hot(self):
        a = _article("1", "reddit", published_ago_h=3,
                     engagement={"upvotes": 2000, "comments": 800})
        score = hotness(a, mentions=4)
        assert heat_level(score) >= 2

    def test_old_story_is_not_hot_even_across_sources(self):
        # Three weeks old: recency gate drives heat to zero regardless of spread.
        a = _article("1", "reddit", published_ago_h=24 * 21,
                     engagement={"upvotes": 5000, "comments": 2000})
        assert heat_level(hotness(a, mentions=5)) == 0

    def test_single_source_quiet_item_is_cool(self):
        a = _article("1", "rss-openai", published_ago_h=10)
        assert heat_level(hotness(a, mentions=1)) == 0

    def test_github_stars_today_drives_velocity(self):
        a = _article("1", "github-trending", published_ago_h=4,
                     engagement={"stars_today": 1500, "stars_total": 4000})
        assert heat_level(hotness(a, mentions=2)) >= 2

    def test_more_sources_never_lowers_heat(self):
        a = _article("1", "reddit", published_ago_h=5,
                     engagement={"upvotes": 500})
        assert hotness(a, mentions=4) >= hotness(a, mentions=1)


class TestHeatLevel:
    def test_bands_are_monotonic(self):
        assert heat_level(0.0) == 0
        assert heat_level(0.2) == 1
        assert heat_level(0.45) == 2
        assert heat_level(0.7) == 3


class TestTopicHeat:
    def test_topic_inherits_its_hottest_items(self):
        hot = _article("1", "reddit", published_ago_h=2,
                       engagement={"upvotes": 3000, "comments": 1200},
                       topic_tags=["ai-agents"])
        cool = _article("2", "rss-openai", published_ago_h=200,
                        topic_tags=["funding"])
        heat = topic_heat([hot, cool], buzz={"1": 4, "2": 1})
        assert heat["ai-agents"] >= 2
        assert heat["funding"] == 0
