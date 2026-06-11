import pytest
from unittest.mock import AsyncMock, MagicMock, patch

YOUTUBE_FEED = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Understanding Transformers</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
    <published>2024-01-01T10:00:00+00:00</published>
    <summary>A deep dive into transformer architecture</summary>
  </entry>
  <entry>
    <title>Second Video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=def456"/>
    <published>2024-01-02T10:00:00+00:00</published>
  </entry>
</feed>"""

EMPTY_FEED = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>"""


@pytest.mark.asyncio
async def test_youtube_parses_feed():
    from app.fetchers.youtube import YouTubeFetcher

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = YOUTUBE_FEED

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await YouTubeFetcher().fetch()

    assert result.ok
    assert len(result.items) > 0
    assert "youtube.com" in result.items[0]["url"]


@pytest.mark.asyncio
async def test_youtube_skips_entries_without_url():
    from app.fetchers.youtube import YouTubeFetcher

    no_link_feed = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><title>No link entry</title></entry>
</feed>"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = no_link_feed

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await YouTubeFetcher().fetch()

    assert result.ok
    assert result.items == []


@pytest.mark.asyncio
async def test_youtube_http_error_per_channel_continues():
    from app.fetchers.youtube import YouTubeFetcher

    call_count = 0

    async def selective_error(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("channel unavailable")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = YOUTUBE_FEED
        return mock_resp

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=selective_error)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await YouTubeFetcher().fetch()

    # Should still return items from channels that didn't fail
    assert result.ok
    assert len(result.items) > 0
