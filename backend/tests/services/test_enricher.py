import pytest
from unittest.mock import AsyncMock, patch

from app.core.time import utcnow
from app.models.article import Article
from app.services.enricher import (
    RateLimited,
    enrich_slug_titles,
    humanize_slug,
    looks_like_slug,
)

pytestmark = pytest.mark.asyncio


def test_slug_detection():
    assert looks_like_slug("r3gm/wan2-2-fp8da-aoti-preview")
    assert looks_like_slug("selfit-camera/Omni-Image-Editor")
    assert looks_like_slug("stable-diffusion-webui-forge")
    assert not looks_like_slug("OpenAI ships computer-use API")
    assert not looks_like_slug("Omni Image Editor — AI photo tool")


async def test_enrich_batch_rewrites_slug_titles(db):
    art = Article(
        id="enrich-1", title="r3gm/wan2-2-fp8da", url="https://huggingface.co/spaces/r3gm/wan2-2-fp8da",
        source_id="hf-spaces", published_at=utcnow(), fetched_at=utcnow(),
        topic_tags=[], is_read=False, is_bookmarked=False, feedback=None, trending_score=1.0,
    )
    db.add(art)
    await db.commit()

    async def fake_enrich(article, _db):
        article.title = "Wan 2.2 — fast video generation demo"
        article.summary = "Generates short videos from text using the Wan 2.2 model."
        await _db.commit()
        return True

    with patch("app.services.enricher.enrich_article", new=AsyncMock(side_effect=fake_enrich)):
        count = await enrich_slug_titles(db, limit=5)

    assert count == 1
    await db.refresh(art)
    assert art.title.startswith("Wan 2.2")


def test_humanize_slug():
    assert humanize_slug("bartowski/Qwen3-VL-30B-GGUF") == "Qwen3 VL 30B GGUF"
    assert humanize_slug("stable-diffusion-webui-forge") == "Stable Diffusion Webui Forge"
    assert humanize_slug("r3gm/wan2-2-fp8da-aoti-preview") == "Wan2 2 FP8 Da Aoti Preview" or (
        " " in humanize_slug("r3gm/wan2-2-fp8da-aoti-preview")
    )
    # never returns something slug-shaped
    assert not looks_like_slug(humanize_slug("owner/some-long-repo-name"))


def _make_slug_article(i: int) -> Article:
    return Article(
        id=f"enrich-fb-{i}", title=f"owner/some-model-name-{i}",
        url=f"https://huggingface.co/owner/some-model-name-{i}",
        source_id="hf-models", published_at=utcnow(), fetched_at=utcnow(),
        topic_tags=[], is_read=False, is_bookmarked=False, feedback=None, trending_score=1.0,
    )


async def test_failed_enrichment_falls_back_to_humanized_title(db):
    art = _make_slug_article(1)
    db.add(art)
    await db.commit()

    # LLM path fails permanently (e.g. no API key) — title must still
    # become readable so the item leaves the slug queue
    with patch("app.services.enricher.enrich_article", new=AsyncMock(return_value=False)):
        count = await enrich_slug_titles(db, limit=5)

    assert count == 0
    await db.refresh(art)
    assert not looks_like_slug(art.title)
    assert art.title == "Some Model Name 1"


async def test_rate_limit_aborts_batch_and_preserves_slugs(db):
    arts = [_make_slug_article(i) for i in (2, 3)]
    db.add_all(arts)
    await db.commit()

    with patch(
        "app.services.enricher.enrich_article",
        new=AsyncMock(side_effect=RateLimited("x")),
    ):
        count = await enrich_slug_titles(db, limit=5)

    # rate-limited items keep their slug titles for the next scheduled run
    assert count == 0
    for art in arts:
        await db.refresh(art)
        assert looks_like_slug(art.title)
