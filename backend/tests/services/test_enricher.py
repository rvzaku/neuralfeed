import pytest
from unittest.mock import AsyncMock, patch

from app.core.time import utcnow
from app.models.article import Article
from app.services.enricher import enrich_slug_titles, looks_like_slug

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
