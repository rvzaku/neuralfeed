from datetime import datetime

from app.schemas.article import ArticleOut


def _base(image_url):
    return ArticleOut(
        id="x", title="t", url="https://e.com", source_id="s", author=None,
        summary=None, image_url=image_url, published_at=datetime(2026, 1, 1),
        fetched_at=datetime(2026, 1, 1), topic_tags=[], is_read=False,
        is_bookmarked=False, feedback=None, trending_score=0.0,
    )


def test_image_url_allows_http_and_https():
    assert _base("https://cdn.example.com/a.png").image_url == "https://cdn.example.com/a.png"
    assert _base("http://cdn.example.com/a.png").image_url == "http://cdn.example.com/a.png"


def test_image_url_rejects_unsafe_schemes():
    assert _base("data:image/png;base64,AAAA").image_url is None
    assert _base("javascript:alert(1)").image_url is None
    assert _base("/relative/path.png").image_url is None
    assert _base(None).image_url is None


def _with_engagement(engagement):
    return ArticleOut(
        id="x", title="t", url="https://e.com", source_id="s", author=None,
        summary=None, image_url=None, published_at=datetime(2026, 1, 1),
        fetched_at=datetime(2026, 1, 1), topic_tags=[], is_read=False,
        is_bookmarked=False, feedback=None, trending_score=0.0,
        engagement=engagement,
    )


def test_engagement_parsed_from_json_string():
    out = _with_engagement('{"stars_total": 1600, "stars_today": 459}')
    assert out.engagement == {"stars_total": 1600, "stars_today": 459}


def test_engagement_clamps_corrupt_star_count():
    # The SVG-path concatenation bug produced ~1e30 stars; it must be dropped,
    # not displayed, even for rows already poisoned in the DB.
    out = _with_engagement({"stars_total": 1_600_161_611_168_257_500_000, "stars_today": 459})
    assert "stars_total" not in out.engagement       # implausible → dropped
    assert out.engagement["stars_today"] == 459       # plausible → kept


def test_engagement_drops_non_numeric_and_negative():
    out = _with_engagement({"upvotes": "lots", "points": -5, "comments": 12})
    assert out.engagement == {"comments": 12}
