from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db, is_guest
from app.models.article import Article
from app.schemas.article import ArticleOut

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/{article_id}/summary")
async def get_summary(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    guest: bool = Depends(is_guest),
) -> dict:
    """Cached-or-generate '5-minute read' summary (single mode since V8).
    Opening it marks the article read.

    Guests are quota-protected: they receive only already-cached summaries, and
    only trigger a fresh (paid) LLM call when guest_summaries_enabled AND the
    global daily guest budget allows — never mutating owner read-state."""
    from app.services import summarizer
    from app.services.summarizer import SummaryError, get_or_generate_summary

    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if guest:
        cached = summarizer.cached_summary(article)
        if cached:
            return {
                "markdown": cached,
                "reading_minutes": summarizer._reading_minutes(cached),
                "cached": True,
                "article_id": article.id,
                "url": article.url,
            }
        if not settings.guest_summaries_enabled or not summarizer.try_consume_guest_summary_budget():
            raise HTTPException(
                status_code=503,
                detail="Sign in to generate a summary — or read the original at the source.",
            )
        # Budget reserved — fall through to generation (no read-state mutation).
        try:
            result = await get_or_generate_summary(article, db)
        except SummaryError as e:
            raise HTTPException(status_code=503, detail=str(e))
        return {**result, "article_id": article.id, "url": article.url}

    try:
        result = await get_or_generate_summary(article, db)
    except SummaryError as e:
        # Frontend falls back to the stored snippet + direct link-out
        raise HTTPException(status_code=503, detail=str(e))

    if user:
        from app.services.user_state import upsert_state
        await upsert_state(db, user.id, article.id, is_read=True)
    elif not article.is_read:
        article.is_read = True
        await db.commit()

    return {**result, "article_id": article.id, "url": article.url}


@router.post("/{article_id}/bookmark", response_model=ArticleOut)
async def toggle_bookmark(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> ArticleOut:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    from app.services.preference_learner import learn

    if user:
        from app.services.user_state import overlay_model, state_map, upsert_state
        current = (await state_map(db, user.id, [article_id])).get(article_id)
        now_bookmarked = not (current.is_bookmarked if current else False)
        state = await upsert_state(db, user.id, article_id, is_bookmarked=now_bookmarked)
        if now_bookmarked:  # saving teaches the ranker; un-saving is just tidying
            await learn(db, user, article, "bookmark")
            await db.commit()
        return overlay_model(ArticleOut.model_validate(article), state)

    article.is_bookmarked = not article.is_bookmarked
    if article.is_bookmarked:
        await learn(db, None, article, "bookmark")
    await db.commit()
    return ArticleOut.model_validate(article)


@router.post("/clear-summary-cache")
async def clear_summary_cache(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    """Drop all cached AI summaries so they regenerate with the current model
    and extraction pipeline. Authenticated users only."""
    if not user:
        raise HTTPException(status_code=401, detail="authentication required")
    result = await db.execute(
        update(Article)
        .where((Article.ai_summary.is_not(None)) | (Article.ai_deep_summary.is_not(None)))
        .values(ai_summary=None, ai_summary_at=None, ai_deep_summary=None, ai_deep_summary_at=None)
    )
    await db.commit()
    return {"cleared": result.rowcount}
