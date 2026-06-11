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
    _parse_llm_json,
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
        body = {"choices": [{"message": {"content": '{"summary": "S", "takeaways": ["a"]}'}}]}
        resp = MagicMock(status_code=200)
        resp.json.return_value = body
        resp.raise_for_status = MagicMock()
        with patch("app.services.summarizer.httpx.AsyncClient", return_value=_mock_async_client(resp)):
            out = await GroqProvider(api_key="k").summarize("t", "c")
        assert out["summary"] == "S"

    @pytest.mark.asyncio
    async def test_groq_http_error_wrapped(self):
        with patch("app.services.summarizer.httpx.AsyncClient",
                   return_value=_mock_async_client(raise_exc=httpx.ConnectError("down"))):
            with pytest.raises(SummaryError, match="groq request failed"):
                await GroqProvider(api_key="k").summarize("t", "c")

    @pytest.mark.asyncio
    async def test_ollama_success(self):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"message": {"content": '{"summary": "S", "takeaways": []}'}}
        resp.raise_for_status = MagicMock()
        with patch("app.services.summarizer.httpx.AsyncClient", return_value=_mock_async_client(resp)):
            out = await OllamaProvider(base_url="http://x", model="m").summarize("t", "c")
        assert out["summary"] == "S"

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


class TestParseLlmJson:
    def test_clean_json(self):
        out = _parse_llm_json('{"summary": "S", "takeaways": ["a", "b", "c"]}')
        assert out == {"summary": "S", "takeaways": ["a", "b", "c"]}

    def test_fenced_json(self):
        out = _parse_llm_json('```json\n{"summary": "S", "takeaways": []}\n```')
        assert out["summary"] == "S"

    def test_caps_takeaways_at_three(self):
        out = _parse_llm_json(json.dumps({"summary": "S", "takeaways": ["1", "2", "3", "4"]}))
        assert len(out["takeaways"]) == 3

    def test_no_json_raises(self):
        with pytest.raises(SummaryError):
            _parse_llm_json("I cannot summarize this.")

    def test_empty_summary_raises(self):
        with pytest.raises(SummaryError):
            _parse_llm_json('{"summary": "", "takeaways": []}')


class TestGetOrGenerateSummary:
    @pytest.mark.asyncio
    async def test_cache_hit_skips_provider(self):
        article = _article(ai_summary=json.dumps({"summary": "cached!", "takeaways": ["x"]}))
        db = AsyncMock()
        with patch("app.services.summarizer.get_provider") as mock_provider:
            result = await get_or_generate_summary(article, db)
        mock_provider.assert_not_called()
        assert result["cached"] is True
        assert result["summary"] == "cached!"

    @pytest.mark.asyncio
    async def test_cache_miss_generates_and_caches(self):
        article = _article()
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(return_value={"summary": "fresh", "takeaways": ["a"]})
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_article_text",
                       new=AsyncMock(return_value="long page text " * 50)):
                result = await get_or_generate_summary(article, db)
        assert result["cached"] is False
        assert json.loads(article.ai_summary)["summary"] == "fresh"
        assert article.ai_summary_at is not None
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_unfetchable_page_falls_back_to_snippet(self):
        article = _article(summary="the stored snippet")
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(return_value={"summary": "from snippet", "takeaways": []})
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_article_text",
                       new=AsyncMock(return_value=None)):
                result = await get_or_generate_summary(article, db)
        provider.summarize.assert_awaited_once()
        assert provider.summarize.await_args.args[1] == "the stored snippet"
        assert result["summary"] == "from snippet"

    @pytest.mark.asyncio
    async def test_no_text_at_all_raises(self):
        article = _article(summary=None)
        db = AsyncMock()
        with patch("app.services.summarizer.extract_article_text",
                   new=AsyncMock(return_value=None)):
            with pytest.raises(SummaryError):
                await get_or_generate_summary(article, db)

    @pytest.mark.asyncio
    async def test_arxiv_uses_abstract_without_page_fetch(self):
        article = _article(source_id="arxiv-cs-ai", summary="the abstract")
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(return_value={"summary": "s", "takeaways": []})
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_article_text") as mock_extract:
                await get_or_generate_summary(article, db)
        mock_extract.assert_not_called()
        assert provider.summarize.await_args.args[1] == "the abstract"

    @pytest.mark.asyncio
    async def test_provider_failure_propagates_and_nothing_cached(self):
        article = _article()
        db = AsyncMock()
        provider = AsyncMock()
        provider.summarize = AsyncMock(side_effect=SummaryError("provider down"))
        with patch("app.services.summarizer.get_provider", return_value=provider):
            with patch("app.services.summarizer.extract_article_text",
                       new=AsyncMock(return_value="text " * 100)):
                with pytest.raises(SummaryError):
                    await get_or_generate_summary(article, db)
        assert article.ai_summary is None
