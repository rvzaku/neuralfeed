import json
from datetime import datetime, timedelta, timezone

from app.services.relevance import (
    apply_daily_caps,
    interleave_by_group,
    popularity,
    relevance_score,
)


def _article(source_id="reddit-ml", days_old=0.0, trending=0.0, engagement=None, aid="x"):
    class A:
        pass
    a = A()
    a.id = aid
    a.source_id = source_id
    a.trending_score = trending
    a.engagement = json.dumps(engagement) if engagement else None
    a.published_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_old)
    return a


class TestPopularity:
    def test_editorial_sources_get_baseline(self):
        assert popularity(_article("rss-openai")) == 0.45

    def test_editorial_with_external_traction_beats_baseline(self):
        # A blog post the community surfaced on HN/Reddit outranks a quiet one
        hot = popularity(_article("rss-openai", engagement={"points": 600, "upvotes": 400}))
        quiet = popularity(_article("rss-openai"))
        assert hot > quiet == 0.45

    def test_editorial_external_traction_never_below_baseline(self):
        # Tiny external numbers must not drag an editorial post below baseline
        assert popularity(_article("rss-openai", engagement={"points": 2})) >= 0.45

    def test_reddit_scales_with_upvotes(self):
        low = popularity(_article(engagement={"upvotes": 10}))
        high = popularity(_article(engagement={"upvotes": 900}))
        assert 0 < low < high <= 1.0

    def test_github_stars_today_beats_stale_total(self):
        velocity = popularity(_article("github-trending", engagement={"stars_today": 300, "stars_total": 500}))
        stale = popularity(_article("github-trending", engagement={"stars_today": 0, "stars_total": 500}))
        assert velocity > stale

    def test_zero_engagement_is_zero(self):
        assert popularity(_article(engagement={"upvotes": 0})) == 0.0

    def test_malformed_engagement_falls_back_to_trending(self):
        a = _article(trending=100)
        a.engagement = "{not json"
        assert popularity(a) > 0


class TestRelevanceScore:
    def test_newer_beats_older_at_equal_popularity(self):
        new = relevance_score(_article(days_old=0, engagement={"upvotes": 100}))
        old = relevance_score(_article(days_old=20, engagement={"upvotes": 100}))
        assert new > old

    def test_popular_old_can_beat_unpopular_new_in_wide_window(self):
        hit = relevance_score(_article(days_old=3, engagement={"upvotes": 800}), window_days=30)
        dud = relevance_score(_article(days_old=0, engagement={"upvotes": 1}), window_days=30)
        assert hit > dud

    def test_year_horizon_ranks_landmark_over_recent_minor(self):
        # V7: opening the app a year later, a months-old landmark (huge traction)
        # must outrank a brand-new minor item — recency nearly vanishes at 365d.
        landmark = relevance_score(
            _article(days_old=180, engagement={"upvotes": 5000}), window_days=365
        )
        minor_new = relevance_score(
            _article(days_old=0, engagement={"upvotes": 5}), window_days=365
        )
        assert landmark > minor_new

    def test_short_window_stays_freshness_led(self):
        # Same comparison in a 1-day view must favor the fresh item (importance
        # weight is 0 for short horizons — original behavior preserved).
        landmark_old = relevance_score(
            _article(days_old=180, engagement={"upvotes": 5000}), window_days=1
        )
        minor_new = relevance_score(
            _article(days_old=0, engagement={"upvotes": 5}), window_days=1
        )
        assert minor_new > landmark_old


class TestDailyCaps:
    def test_caps_per_group_per_day(self):
        articles = [
            _article(aid=f"r{i}", engagement={"upvotes": i}) for i in range(20)
        ]
        kept = apply_daily_caps(articles, per_day=10)
        assert len(kept) == 10
        # the most-upvoted survived
        assert {a.id for a in kept} == {f"r{i}" for i in range(10, 20)}

    def test_groups_capped_independently(self):
        articles = (
            [_article(aid=f"r{i}", engagement={"upvotes": 50}) for i in range(15)]
            + [_article(aid=f"g{i}", source_id="github-trending",
                        engagement={"stars_today": 50}) for i in range(15)]
        )
        kept = apply_daily_caps(articles, per_day=10)
        assert len(kept) == 20

    def test_category_map_pools_subreddits(self):
        articles = (
            [_article(aid=f"a{i}", source_id="reddit-ml", engagement={"upvotes": 100}) for i in range(8)]
            + [_article(aid=f"b{i}", source_id="reddit-localllama", engagement={"upvotes": 100}) for i in range(8)]
        )
        category_of = {"reddit-ml": "social", "reddit-localllama": "social"}
        kept = apply_daily_caps(articles, per_day=10, category_of=category_of)
        assert len(kept) == 10  # one shared budget, not 16


class TestInterleave:
    def test_sources_are_mixed_not_columned(self):
        articles = (
            [_article(aid=f"r{i}", engagement={"upvotes": 100}) for i in range(5)]
            + [_article(aid=f"g{i}", source_id="github-trending",
                        engagement={"stars_today": 100}) for i in range(5)]
        )
        ordered = interleave_by_group(articles)
        assert len(ordered) == 10
        first_four_groups = {a.source_id for a in ordered[:4]}
        assert len(first_four_groups) == 2  # both groups appear immediately

    def test_newest_day_first(self):
        articles = [
            _article(aid="old", days_old=2, engagement={"upvotes": 999}),
            _article(aid="new", days_old=0, engagement={"upvotes": 1}),
        ]
        ordered = interleave_by_group(articles)
        assert ordered[0].id == "new"
