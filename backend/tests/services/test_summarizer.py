import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.models.article import Article
from app.services.summarizer import (
    GroqProvider,
    OllamaProvider,
    SummaryError,
    _html_to_text,
    extract_article_text,
    get_or_generate_summary,
    get_provider,
)


def _mock_async_client(response=None, raise_exc=None):
    client = MagicMock()
    if raise_exc:
        client.get = AsyncMock(side_effect=raise_exc)
        client.post = AsyncMock(side_effect=raise_exc)
    else:
        client.get = AsyncMock(return_value=response)
        client.post = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class TestProviders:
    @pytest.mark.asyncio
    async def test_groq_without_key_raises(self):
        with patch("app.services.summarizer.settings") as mock_settings:
            mock_settings.groq_api_key = ""
            mock_settings.summary_model = ""
            provider = GroqProvider(api_key="")
            with pytest.raises(SummaryError, match="GROQ_API_KEY"):
                await provider.summarize("t", "c")

    @pytest.mark.asyncio
    async def test_groq_success(self):
        body = {"choices": [{"message": {"content": "A clear story about the model. " * 20}}]}
        resp = MagicMock(status_code=200)
        resp.json.return_value = body
        resp.raise_for_status = MagicMock()
        with patch("app.services.summarizer.httpx.AsyncClient", return_value=_mock_async_client(resp)):
            out = await GroqProvider(api_key="k").summarize("t", "c")
        assert "clear story" in out

    @pytest.mark.asyncio
    async def test_groq_http_error_wrapped(self):
        with patch("app.services.summarizer.httpx.AsyncClient",
                   return_value=_mock_async_client(raise_exc=httpx.ConnectError("down"))):
            with pytest.raises(SummaryError, match="groq request failed"):
                await GroqProvider(api_key="k").summarize("t", "c")

    @pytest.mark.asyncio
    async def test_ollama_success(self):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"message": {"content": "A clear story about the model. " * 20}}
        resp.raise_for_status = MagicMock()
        with patch("app.services.summarizer.httpx.AsyncClient", return_value=_mock_async_client(resp)):
            out = await OllamaProvider(base_url="http://x", model="m").summarize("t", "c")
        assert "clear story" in out

    def test_get_provider_default_is_groq(self):
        assert isinstance(get_provider(), GroqProvider)


class TestExtraction:
    def test_html_to_text_strips_scripts(self):
        html = "<html><script>evil()</script><p>Real content here</p></html>"
        assert "evil" not in _html_to_text(html)
        assert "Real content here" in _html_to_text(html)

    @pytest.mark.asyncio
    async def test_non_html_content_returns_none(self):
        resp = MagicMock(status_code=200, headers={"content-type": "application/pdf"})
        resp.raise_for_status = MagicMock()
        with patch("app.services.summarizer.httpx.AsyncClient", return_value=_mock_async_client(resp)):
            assert await extract_article_text("https://example.com/x.pdf") is None

    @pytest.mark.asyncio
    async def test_fetch_failure_returns_none(self):
        with patch("app.services.summarizer.httpx.AsyncClient",
                   return_value=_mock_async_client(raise_exc=httpx.ConnectError("nope"))):
            assert await extract_article_text("https://example.com/x") is None


def _article(**kw):
    defaults = dict(
        id="abc123",
        title="Qwen 3 released",
        url="https://example.com/qwen3",
        source_id="rss-openai",
        summary="A short snippet about Qwen 3.",
        published_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        topic_tags=[],
        is_read=False,
        is_bookmarked=False,
        trending_score=0.0,
    )
    defaults.update(kw)
    return Article(**defaults)


class TestGetOrGenerateSummary:
    @pytest.mark.asyncio
    async def test_markdown_cache_hit_skips_provider(self):
        article = _article(ai_summary="Cached five-minute story.")
        db = AsyncMock()
        with patch("app.services.summarizer.get_provider") as mock_provider:
            result = await get_or_generate_summary(article, db)
        mock_provider.assert_not_called()
        assert result["cached"] is True
        assert result["markdown"] == "Cached five-minute story."

    @pytest.mark.asyncio
    async def test_legacy_json_cache_is_regenerated(self):
        # Pre-V8 caches were JSON blobs — they must not render verbatim
        article = _article(ai_summary=json.dumps({"summary": "old", "takeaways": []}))
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(return_value="A fresh free-form summary.")
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_content_for",
                       new=AsyncMock(return_value="page text " * 50)):
                result = await get_or_generate_summary(article, db)
        assert result["cached"] is False
        assert article.ai_summary == "A fresh free-form summary."

    @pytest.mark.asyncio
    async def test_cache_miss_generates_and_caches_markdown(self):
        article = _article()
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(return_value="fresh markdown")
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_content_for",
                       new=AsyncMock(return_value="long page text " * 50)):
                result = await get_or_generate_summary(article, db)
        assert result["cached"] is False
        assert article.ai_summary == "fresh markdown"
        assert article.ai_summary_at is not None
        assert result["reading_minutes"] >= 1
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_unfetchable_page_falls_back_to_snippet(self):
        article = _article(summary="the stored snippet")
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(return_value="from snippet")
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_content_for",
                       new=AsyncMock(return_value=None)):
                result = await get_or_generate_summary(article, db)
        provider.summarize.assert_awaited_once()
        assert "the stored snippet" in provider.summarize.await_args.args[1]
        assert result["markdown"] == "from snippet"

    @pytest.mark.asyncio
    async def test_arxiv_abstract_is_included_in_content(self):
        article = _article(source_id="arxiv-cs-ai", summary="the abstract")
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(return_value="s")
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_content_for",
                       new=AsyncMock(return_value="page body")):
                await get_or_generate_summary(article, db)
        assert "the abstract" in provider.summarize.await_args.args[1]

    @pytest.mark.asyncio
    async def test_provider_failure_propagates_and_nothing_cached(self):
        article = _article()
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(side_effect=SummaryError("provider down"))
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_content_for",
                       new=AsyncMock(return_value="text " * 100)):
                with pytest.raises(SummaryError):
                    await get_or_generate_summary(article, db)
        assert article.ai_summary is None
