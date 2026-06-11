import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.models.article import Article
from app.services.summarizer import (
    SummaryError,
    _parse_llm_json,
    get_or_generate_summary,
)


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
