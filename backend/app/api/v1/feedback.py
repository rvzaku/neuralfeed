from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.schemas.feedback import FeedbackIn
from app.services.feedback_service import ArticleNotFound, apply_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=200)
async def post_feedback(
    body: FeedbackIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    try:
        article = await apply_feedback(body.article_id, body.value, db)
    except ArticleNotFound:
        raise HTTPException(status_code=404, detail="Article not found")

    value = article.feedback
    if user:
        from app.services.user_state import upsert_state
        state = await upsert_state(db, user.id, body.article_id, feedback=body.value or None)
        value = state.feedback
    return {"ok": True, "article_id": body.article_id, "feedback": value}
