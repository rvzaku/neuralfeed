import pytest
from unittest.mock import AsyncMock, MagicMock, patch

RSS_FEED = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>karpathy / Nitter</title>
    <item>
      <title>Interesting paper on LLMs</title>
      <link>https://nitter.net/karpathy/status/123</link>
      <pubDate>Mon, 01 Jan 2024 10:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""

EMPTY_FEED = """<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>"""


@pytest.mark.asyncio
async def test_nitter_parses_feed():
    from app.fetchers.nitter import NitterFetcher

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = RSS_FEED

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        fetcher = NitterFetcher(accounts=["karpathy"])
        result = await fetcher.fetch()

    assert result.ok
    assert len(result.items) >= 1
    assert result.items[0]["title"] == "Interesting paper on LLMs"


@pytest.mark.asyncio
async def test_nitter_empty_feed_returns_empty():
    from app.fetchers.nitter import NitterFetcher

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = EMPTY_FEED

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        fetcher = NitterFetcher(accounts=["karpathy"])
        result = await fetcher.fetch()

    assert result.ok
    assert result.items == []


@pytest.mark.asyncio
async def test_nitter_http_error_degrades_gracefully():
    from app.fetchers.nitter import NitterFetcher

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        fetcher = NitterFetcher(accounts=["karpathy"])
        result = await fetcher.fetch()

    # All instances failed — returns ok=True with empty items (graceful degradation)
    assert result.ok
    assert result.items == []


@pytest.mark.asyncio
async def test_nitter_uses_explicit_accounts():
    from app.fetchers.nitter import NitterFetcher

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = RSS_FEED

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        fetcher = NitterFetcher(accounts=["testuser"])
        result = await fetcher.fetch()

    assert result.ok
    # author should be @testuser
    assert result.items[0]["author"] == "@testuser"
