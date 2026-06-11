import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.fetchers.github_trending import GithubTrendingFetcher

SAMPLE_HTML = """
<html><body>
<article class="Box-row">
  <h2>
    <a class="lh-condensed" href="/openai/gpt-neo">
      openai / gpt-neo
    </a>
  </h2>
  <p class="col-9 text-gray my-1 pr-4">
    An open-source alternative to GPT-3
  </p>
</article>
<article class="Box-row">
  <h2>
    <a class="lh-condensed" href="/huggingface/transformers">
      huggingface / transformers
    </a>
  </h2>
  <p class="col-9 text-gray my-1 pr-4">
    State-of-the-art Machine Learning for JAX, PyTorch and TensorFlow
  </p>
</article>
</body></html>
"""


def _mock_client(text="", raise_on_get=None):
    resp = MagicMock()
    resp.status_code = 200
    resp.text = text
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
async def test_github_trending_parses_repos():
    fetcher = GithubTrendingFetcher()
    with patch("app.fetchers.github_trending.httpx.AsyncClient", return_value=_mock_client(SAMPLE_HTML)):
        result = await fetcher.fetch()

    assert result.ok
    assert result.source_id == "github-trending"
    assert len(result.items) == 2
    urls = [i["url"] for i in result.items]
    assert "https://github.com/openai/gpt-neo" in urls
    assert "https://github.com/huggingface/transformers" in urls


@pytest.mark.asyncio
async def test_github_trending_description_captured():
    fetcher = GithubTrendingFetcher()
    with patch("app.fetchers.github_trending.httpx.AsyncClient", return_value=_mock_client(SAMPLE_HTML)):
        result = await fetcher.fetch()

    neo = next(i for i in result.items if "gpt-neo" in i["url"])
    assert neo["summary"] is not None
    assert "GPT-3" in neo["summary"]


@pytest.mark.asyncio
async def test_github_trending_empty_page():
    fetcher = GithubTrendingFetcher()
    with patch(
        "app.fetchers.github_trending.httpx.AsyncClient",
        return_value=_mock_client("<html><body></body></html>"),
    ):
        result = await fetcher.fetch()

    assert result.ok
    assert result.items == []


@pytest.mark.asyncio
async def test_github_trending_http_error():
    fetcher = GithubTrendingFetcher()
    with patch(
        "app.fetchers.github_trending.httpx.AsyncClient",
        return_value=_mock_client(raise_on_get=Exception("403 Forbidden")),
    ):
        result = await fetcher.fetch()

    assert not result.ok
    assert result.error is not None
