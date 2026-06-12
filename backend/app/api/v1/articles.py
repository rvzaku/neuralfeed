from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.article import Article
from app.schemas.article import ArticleOut

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/{article_id}/summary")
async def get_summary(
    article_id: str,
    mode: str = Query("quick", pattern="^(quick|deep)$"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    """Cached-or-generate summary. quick = 1-minute; deep = 10-minute markdown
    brief. Opening either marks the article read."""
    from app.services.summarizer import SummaryError, get_or_generate_summary

    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    try:
        result = await get_or_generate_summary(article, db, mode=mode)
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

    if user:
        from app.services.user_state import overlay, state_map, upsert_state
        current = (await state_map(db, user.id, [article_id])).get(article_id)
        state = await upsert_state(
            db, user.id, article_id,
            is_bookmarked=not (current.is_bookmarked if current else False),
        )
        out = ArticleOut.model_validate(article).model_dump()
        return ArticleOut(**overlay(out, state))

    article.is_bookmarked = not article.is_bookmarked
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
