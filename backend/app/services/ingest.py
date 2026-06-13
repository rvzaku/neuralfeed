import json
import re
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

        # Dedup 1: URL-exact — but refresh the engagement stats, which is the
        # whole point of re-fetching hot/top listings (V7 relevance ranking)
        article_id = make_article_id(source_id, url)
        existing = await db.get(Article, article_id)
        if existing:
            new_score = float(raw.get("trending_score", 0.0))
            # Refresh to the CURRENT value, not the all-time peak. Velocity
            # metrics like GitHub "stars today" fall as well as rise, so a
            # ratchet would freeze a repo at its busiest day forever. Only an
            # empty/failed re-fetch (score 0) preserves the prior number.
            if new_score > 0:
                existing.trending_score = new_score
            if raw.get("engagement"):
                existing.engagement = json.dumps(raw["engagement"])
                existing.engagement_at = now
            # V9: backfill the REAL release date onto rows stamped with fetch
            # time before the fetchers learned true created_at dates — the
            # user only ever cares about original publication time
            raw_published = raw.get("published_at")
            if raw_published and abs((existing.published_at - existing.fetched_at).total_seconds()) < 120:
                try:
                    from dateutil import parser as dtparser
                    real = to_naive_utc(dtparser.parse(raw_published) if isinstance(raw_published, str) else raw_published)
                    if abs((real - existing.published_at).total_seconds()) > 3600:
                        existing.published_at = real
                except Exception:
                    pass
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
            engagement=json.dumps(raw["engagement"]) if raw.get("engagement") else None,
            engagement_at=now if raw.get("engagement") else None,
        )
        try:
            async with db.begin_nested():  # savepoint — only rolls back this one article
                db.add(article)
            inserted += 1
        except IntegrityError:
            log.debug("ingest_skip_duplicate", source_id=source_id, url=url)

    # Engagement refreshes on existing rows also need flushing
    await db.commit()
    if inserted:
        source = await db.get(Source, source_id)
        if source:
            source.last_fetched_at = now
            await db.commit()

    # HF Daily Papers is curated traction — propagate its upvotes onto the
    # matching raw arxiv-* articles so the relevance ranker can tell papers
    # gaining attention apart from the daily firehose (V7).
    if source_id == "hf-papers":
        await _boost_arxiv_traction(items, db)

    log.info("ingest_complete", source_id=source_id, inserted=inserted, total=len(items))
    return inserted


_ARXIV_ID_RE = re.compile(r"arxiv\.org/abs/([0-9.v]+)")


async def _boost_arxiv_traction(items: list[dict], db: AsyncSession) -> None:
    boosted = 0
    for raw in items:
        m = _ARXIV_ID_RE.search(raw.get("url", ""))
        if not m:
            continue
        upvotes = float(raw.get("trending_score", 0.0))
        if upvotes <= 0:
            continue
        result = await db.execute(
            select(Article).where(
                Article.source_id.like("arxiv-%"),
                Article.url.contains(m.group(1)),
            )
        )
        for article in result.scalars().all():
            if upvotes > article.trending_score:
                article.trending_score = upvotes
                boosted += 1
    if boosted:
        await db.commit()
        log.info("arxiv_traction_boosted", count=boosted)
