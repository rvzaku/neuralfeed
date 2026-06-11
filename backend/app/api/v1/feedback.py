from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.feedback import FeedbackIn
from app.services.feedback_service import ArticleNotFound, apply_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=200)
async def post_feedback(body: FeedbackIn, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        article = await apply_feedback(body.article_id, body.value, db)
    except ArticleNotFound:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"ok": True, "article_id": body.article_id, "feedback": article.feedback}
