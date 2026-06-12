import structlog
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import to_naive_utc, utcnow
from app.models.article import Article, make_article_id, make_title_hash
from app.models.source import Source
from app.services.topic_tagger import tag_topics

log = structlog.get_logger()


def _truncate(text: Optional[str], max_len: int = 500) -> Optional[str]:
    if not text:
        return None
    return text[:max_len].rstrip() + ("…" if len(text) > max_len else "")


async def ingest_items(items: list[dict], source_id: str, db: AsyncSession) -> int:
    """Normalise, dedup, and persist a list of raw fetched items. Returns count inserted."""
    inserted = 0
    now = utcnow()

    for raw in items:
        url = raw.get("url", "").strip()
        if not url:
            continue

        # Dedup 1: URL-exact (primary key collision)
        article_id = make_article_id(source_id, url)
        if await db.get(Article, article_id):
            continue

        title = raw.get("title", "").strip()[:512]

        # Dedup 2: title-similarity within the same source
        title_hash = make_title_hash(title) if title else None
        if title_hash:
            dup = (await db.execute(
                select(Article).where(
                    Article.source_id == source_id,
                    Article.title_hash == title_hash,
                ).limit(1)
            )).scalar_one_or_none()
            if dup:
                continue

        summary = _truncate(raw.get("summary"))
        topic_tags = tag_topics(f"{title} {summary or ''}")

        try:
            published_at = raw.get("published_at") or now
            if isinstance(published_at, str):
                from dateutil import parser as dtparser
                published_at = dtparser.parse(published_at)
            published_at = to_naive_utc(published_at)
        except Exception:
            published_at = now

        article = Article(
            id=article_id,
            title=title,
            url=url,
            source_id=source_id,
            author=raw.get("author"),
            summary=summary,
            image_url=raw.get("image_url") or None,
            published_at=published_at,
            fetched_at=now,
            topic_tags=topic_tags,
            is_read=False,
            is_bookmarked=False,
            feedback=None,
            trending_score=float(raw.get("trending_score", 0.0)),
            title_hash=title_hash,
        )
        try:
            async with db.begin_nested():  # savepoint — only rolls back this one article
                db.add(article)
            inserted += 1
        except IntegrityError:
            log.debug("ingest_skip_duplicate", source_id=source_id, url=url)

    if inserted:
        await db.commit()
        source = await db.get(Source, source_id)
        if source:
            source.last_fetched_at = now
            await db.commit()

    log.info("ingest_complete", source_id=source_id, inserted=inserted, total=len(items))
    return inserted
