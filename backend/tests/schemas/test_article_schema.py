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
