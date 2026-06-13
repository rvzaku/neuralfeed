"""V8 single-mode summary: source-type extraction routing + no-content guard.

(The separate 'deep' mode was removed per app-feedback-v5; the source-aware
extractors now feed the one 5-minute summary, so routing stays covered.)
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.time import utcnow
from app.models.article import Article, make_title_hash
from app.services import summarizer

MD = "**TL;DR:** A quick take.\n\n## What it is\n" + ("word " * 200)


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
async def test_summary_routes_reddit_to_thread_extractor(db):
    article = await _persist(db, _article("v8r", "https://reddit.com/r/ml/comments/x/y/", "reddit-ml"))
    provider = AsyncMock()
    provider.summarize = AsyncMock(return_value=MD)

    with patch.object(summarizer, "get_provider", return_value=provider), \
         patch.object(summarizer, "_extract_reddit_thread",
                      new=AsyncMock(return_value="post body\nCOMMENT: insightful " * 30)) as ext:
        await summarizer.get_or_generate_summary(article, db)
    ext.assert_awaited_once()


@pytest.mark.asyncio
async def test_summary_routes_github_to_readme(db):
    article = await _persist(db, _article("v8g", "https://github.com/org/repo", "github-trending"))
    provider = AsyncMock()
    provider.summarize = AsyncMock(return_value=MD)

    with patch.object(summarizer, "get_provider", return_value=provider), \
         patch.object(summarizer, "_extract_github_readme",
                      new=AsyncMock(return_value="# Repo\n" + "docs " * 100)) as ext:
        await summarizer.get_or_generate_summary(article, db)
    ext.assert_awaited_once()


@pytest.mark.asyncio
async def test_summary_generated_once_then_cached(db):
    article = await _persist(db, _article("v8c", "https://openai.com/blog/x"))
    provider = AsyncMock()
    provider.summarize = AsyncMock(return_value=MD)

    with patch.object(summarizer, "get_provider", return_value=provider), \
         patch.object(summarizer, "extract_article_text", new=AsyncMock(return_value="content " * 100)):
        first = await summarizer.get_or_generate_summary(article, db)
        second = await summarizer.get_or_generate_summary(article, db)

    assert first["cached"] is False and second["cached"] is True
    assert second["markdown"] == MD
    assert first["reading_minutes"] >= 1
    provider.summarize.assert_awaited_once()
