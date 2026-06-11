from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.article import Article
from app.schemas.article import ArticleOut

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("/{article_id}/bookmark", response_model=ArticleOut)
async def toggle_bookmark(article_id: str, db: AsyncSession = Depends(get_db)) -> ArticleOut:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.is_bookmarked = not article.is_bookmarked
    await db.commit()
    return ArticleOut.model_validate(article)
