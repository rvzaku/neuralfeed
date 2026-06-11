"""Deep summaries: caching, source-type extraction routing, provider contract."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.time import utcnow
from app.models.article import Article, make_title_hash
from app.services import summarizer

DEEP_MD = "## Context\n" + ("word " * 450)  # plausibly long markdown


def _article(article_id, url, source_id="rss-openai", summary="snippet"):
    return Article(
        id=article_id, title=f"T {article_id}", url=url, source_id=source_id,
        author=None, summary=summary, published_at=utcnow(), fetched_at=utcnow(),
        topic_tags=["llm"], is_read=False, is_bookmarked=False, feedback=None,
        trending_score=0.0, title_hash=make_title_hash(article_id),
    )


async def _persist(db, article):
    db.add(article)
    await db.commit()
    return article


@pytest.mark.asyncio
async def test_deep_summary_generated_and_cached(db):
    article = await _persist(db, _article("deep1", "https://openai.com/blog/x"))
    provider = AsyncMock()
    provider.summarize_deep = AsyncMock(return_value=DEEP_MD)

    with patch.object(summarizer, "get_provider", return_value=provider), \
         patch.object(summarizer, "extract_article_text", new=AsyncMock(return_value="content " * 100)):
        first = await summarizer.get_or_generate_summary(article, db, mode="deep")
        second = await summarizer.get_or_generate_summary(article, db, mode="deep")

    assert first["cached"] is False and second["cached"] is True
    assert second["markdown"] == DEEP_MD
    assert first["reading_minutes"] >= 2
    assert article.ai_deep_summary == DEEP_MD
    assert article.ai_deep_summary_at is not None
    provider.summarize_deep.assert_awaited_once()  # cache hit skips the provider


@pytest.mark.asyncio
async def test_deep_routes_reddit_to_thread_extractor(db):
    article = await _persist(db, _article("deep2", "https://reddit.com/r/ml/comments/x/y/", "reddit-ml"))
    provider = AsyncMock()
    provider.summarize_deep = AsyncMock(return_value=DEEP_MD)

    with patch.object(summarizer, "get_provider", return_value=provider), \
         patch.object(summarizer, "_extract_reddit_thread",
                      new=AsyncMock(return_value="post body\nCOMMENT: insightful " * 30)) as ext:
        await summarizer.get_or_generate_summary(article, db, mode="deep")
    ext.assert_awaited_once()


@pytest.mark.asyncio
async def test_deep_routes_github_to_readme(db):
    article = await _persist(db, _article("deep3", "https://github.com/org/repo", "github-trending"))
    provider = AsyncMock()
    provider.summarize_deep = AsyncMock(return_value=DEEP_MD)

    with patch.object(summarizer, "get_provider", return_value=provider), \
         patch.object(summarizer, "_extract_github_readme",
                      new=AsyncMock(return_value="# Repo\n" + "docs " * 100)) as ext:
        await summarizer.get_or_generate_summary(article, db, mode="deep")
    ext.assert_awaited_once()


@pytest.mark.asyncio
async def test_deep_no_content_raises(db):
    article = await _persist(db, _article("deep4", "https://dead.example/x", summary=None))
    with patch.object(summarizer, "extract_article_text", new=AsyncMock(return_value=None)):
        with pytest.raises(summarizer.SummaryError):
            await summarizer.get_or_generate_summary(article, db, mode="deep")


@pytest.mark.asyncio
async def test_quick_mode_unchanged(db):
    article = await _persist(db, _article("deep5", "https://openai.com/blog/y"))
    provider = AsyncMock()
    provider.summarize = AsyncMock(return_value={"summary": "s", "takeaways": ["a"]})

    with patch.object(summarizer, "get_provider", return_value=provider), \
         patch.object(summarizer, "extract_article_text", new=AsyncMock(return_value="content " * 100)):
        result = await summarizer.get_or_generate_summary(article, db)
    assert result["summary"] == "s" and result["cached"] is False
