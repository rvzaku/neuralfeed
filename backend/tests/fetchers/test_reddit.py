import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.fetchers.reddit import RedditFetcher

SAMPLE_REDDIT_JSON = {
    "data": {
        "children": [
            {
                "data": {
                    "title": "GPT-5 Released",
                    "permalink": "/r/MachineLearning/comments/abc123/gpt5_released/",
                    "url": "https://openai.com/gpt5",
                    "author": "ml_fan",
                    "score": 1500,
                    "is_self": False,
                    "stickied": False,
                    "selftext": "",
                    "created_utc": 1704067200.0,
                }
            },
            {
                "data": {
                    "title": "Discussion: Best fine-tuning approaches",
                    "permalink": "/r/MachineLearning/comments/def456/discussion_finetuning/",
                    "url": "https://www.reddit.com/r/MachineLearning/comments/def456/",
                    "author": "researcher42",
                    "score": 300,
                    "is_self": True,
                    "stickied": False,
                    "selftext": "Let's discuss fine-tuning approaches for large models.",
                    "created_utc": 1704060000.0,
                }
            },
            {
                "data": {
                    "title": "Stickied announcement",
                    "permalink": "/r/MachineLearning/comments/sticky/",
                    "url": "https://reddit.com/sticky",
                    "author": "mod",
                    "score": 0,
                    "is_self": True,
                    "stickied": True,
                    "selftext": "",
                    "created_utc": 1704000000.0,
                }
            },
        ]
    }
}


def _mock_client(json_data=None, raise_on_get=None):
    resp = MagicMock()
    resp.status_code = 200
    resp.json = MagicMock(return_value=json_data or {})
    resp.raise_for_status = MagicMock()
    client = AsyncMock()
    if raise_on_get:
        client.get = AsyncMock(side_effect=raise_on_get)
    else:
        client.get = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.mark.asyncio
async def test_reddit_parses_posts():
    fetcher = RedditFetcher("reddit-ml")
    with patch("app.fetchers.reddit.httpx.AsyncClient", return_value=_mock_client(SAMPLE_REDDIT_JSON)):
        result = await fetcher.fetch()

    assert result.ok
    assert result.source_id == "reddit-ml"
    # stickied post must be excluded
    assert len(result.items) == 2
    titles = [i["title"] for i in result.items]
    assert "GPT-5 Released" in titles
    assert "Stickied announcement" not in titles


@pytest.mark.asyncio
async def test_reddit_self_post_uses_permalink():
    fetcher = RedditFetcher("reddit-ml")
    with patch("app.fetchers.reddit.httpx.AsyncClient", return_value=_mock_client(SAMPLE_REDDIT_JSON)):
        result = await fetcher.fetch()

    self_post = next(i for i in result.items if "Discussion" in i["title"])
    assert "reddit.com" in self_post["url"]
    assert self_post["summary"] is not None


@pytest.mark.asyncio
async def test_reddit_published_at_set_from_epoch():
    fetcher = RedditFetcher("reddit-ml")
    with patch("app.fetchers.reddit.httpx.AsyncClient", return_value=_mock_client(SAMPLE_REDDIT_JSON)):
        result = await fetcher.fetch()

    for item in result.items:
        assert item["published_at"] is not None


@pytest.mark.asyncio
async def test_reddit_unknown_subreddit_returns_error():
    fetcher = RedditFetcher("reddit-unknown")
    result = await fetcher.fetch()
    assert not result.ok
    assert result.error is not None


@pytest.mark.asyncio
async def test_reddit_http_error_falls_back_to_rss():
    """JSON failure must trigger the RSS fallback; if that also fails, error out."""
    fetcher = RedditFetcher("reddit-ml")
    with patch(
        "app.fetchers.reddit.httpx.AsyncClient",
        return_value=_mock_client(raise_on_get=Exception("timeout")),
    ):
        with patch(
            "app.fetchers.reddit.urllib.request.urlopen",
            side_effect=Exception("rss also blocked"),
        ):
            result = await fetcher.fetch()

    assert not result.ok
    assert "rss also blocked" in result.error


@pytest.mark.asyncio
async def test_reddit_rss_fallback_parses_entries():
    rss_body = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Qwen 3 released</title>
        <link href="https://www.reddit.com/r/MachineLearning/comments/xyz/qwen3/"/>
        <author><name>/u/ml_fan</name></author>
        <updated>2026-06-10T12:00:00+00:00</updated>
      </entry>
    </feed>"""
    fetcher = RedditFetcher("reddit-ml")
    mock_resp = MagicMock()
    mock_resp.read.return_value = rss_body.encode()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch(
        "app.fetchers.reddit.httpx.AsyncClient",
        return_value=_mock_client(raise_on_get=Exception("403 Blocked")),
    ):
        with patch("app.fetchers.reddit.urllib.request.urlopen", return_value=mock_resp):
            result = await fetcher.fetch()

    assert result.ok
    assert len(result.items) == 1
    assert result.items[0]["title"] == "Qwen 3 released"
