import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.fetchers.arxiv import ArxivFetcher

SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>https://arxiv.org/abs/2401.00001v1</id>
    <title>Attention Is All You Need Again</title>
    <summary>A new study on transformer architectures.</summary>
    <author><name>Jane Doe</name></author>
    <published>2024-01-15T00:00:00Z</published>
    <link href="https://arxiv.org/abs/2401.00001v1" rel="alternate"/>
  </entry>
  <entry>
    <id>https://arxiv.org/abs/2401.00002v1</id>
    <title>Scaling Laws Revisited</title>
    <summary>Empirical study of scaling behaviour.</summary>
    <author><name>John Smith</name></author>
    <published>2024-01-14T00:00:00Z</published>
    <link href="https://arxiv.org/abs/2401.00002v1" rel="alternate"/>
  </entry>
</feed>
"""

EMPTY_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>
"""


def _mock_client(status=200, text=""):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.raise_for_status = MagicMock()
    client = AsyncMock()
    client.get = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.mark.asyncio
async def test_arxiv_parses_items():
    fetcher = ArxivFetcher("arxiv-cs-ai")
    with patch("app.fetchers.arxiv.httpx.AsyncClient", return_value=_mock_client(text=SAMPLE_ATOM)):
        result = await fetcher.fetch()

    assert result.ok
    assert result.source_id == "arxiv-cs-ai"
    assert len(result.items) == 2
    assert result.items[0]["title"] == "Attention Is All You Need Again"
    assert result.items[0]["author"] == "Jane Doe"
    assert "arxiv.org/abs" in result.items[0]["url"]


@pytest.mark.asyncio
async def test_arxiv_empty_feed():
    fetcher = ArxivFetcher("arxiv-cs-cv")
    with patch("app.fetchers.arxiv.httpx.AsyncClient", return_value=_mock_client(text=EMPTY_ATOM)):
        result = await fetcher.fetch()

    assert result.ok
    assert result.source_id == "arxiv-cs-cv"
    assert result.items == []


@pytest.mark.asyncio
async def test_arxiv_http_error():
    fetcher = ArxivFetcher("arxiv-cs-ai")
    client = AsyncMock()
    client.get = AsyncMock(side_effect=Exception("connection refused"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    with patch("app.fetchers.arxiv.httpx.AsyncClient", return_value=client):
        result = await fetcher.fetch()

    assert not result.ok
    assert "connection refused" in result.error


@pytest.mark.asyncio
async def test_arxiv_malformed_xml():
    fetcher = ArxivFetcher("arxiv-cs-ai")
    with patch("app.fetchers.arxiv.httpx.AsyncClient", return_value=_mock_client(text="<not valid xml<<")):
        result = await fetcher.fetch()

    assert not result.ok
    assert result.error is not None
