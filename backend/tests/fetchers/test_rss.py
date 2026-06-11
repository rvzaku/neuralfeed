import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.fetchers.rss import RSSFetcher

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>OpenAI Blog</title>
    <link>https://openai.com/blog</link>
    <item>
      <title>Introducing GPT-5</title>
      <link>https://openai.com/blog/gpt-5</link>
      <description>GPT-5 is our most capable model yet.</description>
      <author>OpenAI</author>
      <pubDate>Mon, 15 Jan 2024 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Safety research update</title>
      <link>https://openai.com/blog/safety-update</link>
      <description>Our latest alignment work.</description>
      <pubDate>Sun, 14 Jan 2024 10:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""

EMPTY_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Empty</title></channel></rss>
"""


def _mock_client(text="", status=200, raise_on_get=None):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.raise_for_status = MagicMock(
        side_effect=Exception(f"HTTP {status}") if status >= 400 else None
    )
    client = AsyncMock()
    if raise_on_get:
        client.get = AsyncMock(side_effect=raise_on_get)
    else:
        client.get = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.mark.asyncio
async def test_rss_parses_items():
    fetcher = RSSFetcher("rss-openai", feed_url="https://openai.com/blog/rss.xml")
    with patch("app.fetchers.rss.httpx.AsyncClient", return_value=_mock_client(SAMPLE_RSS)):
        result = await fetcher.fetch()

    assert result.ok
    assert result.source_id == "rss-openai"
    assert len(result.items) == 2
    titles = [i["title"] for i in result.items]
    assert "Introducing GPT-5" in titles
    assert "Safety research update" in titles


@pytest.mark.asyncio
async def test_rss_item_fields():
    fetcher = RSSFetcher("rss-openai", feed_url="https://openai.com/blog/rss.xml")
    with patch("app.fetchers.rss.httpx.AsyncClient", return_value=_mock_client(SAMPLE_RSS)):
        result = await fetcher.fetch()

    item = result.items[0]
    assert item["url"].startswith("https://openai.com/blog/")
    assert item["summary"] is not None
    assert item["published_at"] is not None


@pytest.mark.asyncio
async def test_rss_empty_feed():
    fetcher = RSSFetcher("rss-openai", feed_url="https://openai.com/blog/rss.xml")
    with patch("app.fetchers.rss.httpx.AsyncClient", return_value=_mock_client(EMPTY_RSS)):
        result = await fetcher.fetch()

    assert result.ok
    assert result.items == []


@pytest.mark.asyncio
async def test_rss_no_feed_url_returns_error():
    fetcher = RSSFetcher("rss-unknown-source")
    result = await fetcher.fetch()
    assert not result.ok
    assert result.error is not None


@pytest.mark.asyncio
async def test_rss_http_error():
    fetcher = RSSFetcher("rss-openai", feed_url="https://openai.com/blog/rss.xml")
    with patch(
        "app.fetchers.rss.httpx.AsyncClient",
        return_value=_mock_client(raise_on_get=Exception("connection timeout")),
    ):
        result = await fetcher.fetch()

    assert not result.ok
    assert "connection timeout" in result.error
