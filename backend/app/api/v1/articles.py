from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.article import Article
from app.schemas.article import ArticleOut

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/{article_id}/summary")
async def get_summary(
    article_id: str,
    mode: str = Query("quick", pattern="^(quick|deep)$"),
    db: AsyncSession = Depends(get_db),
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

    if not article.is_read:
        article.is_read = True
        await db.commit()

    return {**result, "article_id": article.id, "url": article.url}


@router.post("/{article_id}/bookmark", response_model=ArticleOut)
async def toggle_bookmark(article_id: str, db: AsyncSession = Depends(get_db)) -> ArticleOut:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.is_bookmarked = not article.is_bookmarked
    await db.commit()
    return ArticleOut.model_validate(article)
