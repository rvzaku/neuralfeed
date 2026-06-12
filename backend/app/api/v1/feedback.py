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
    # Capture pre-update reaction so toggling a like off reverses the learning
    previous = None
    if user:
        from app.services.user_state import state_map
        prev_state = (await state_map(db, user.id, [body.article_id])).get(body.article_id)
        previous = prev_state.feedback if prev_state else None

    try:
        article = await apply_feedback(body.article_id, body.value, db)
    except ArticleNotFound:
        raise HTTPException(status_code=404, detail="Article not found")

    value = article.feedback
    if user:
        from app.services.user_state import upsert_state
        state = await upsert_state(db, user.id, body.article_id, feedback=body.value or None)
        value = state.feedback

    # V8: thumbs teach the ranker (replaces manual weight sliders)
    if body.value in (1, -1):
        from app.services.preference_learner import learn
        signal = "like" if body.value == 1 else "dislike"
        await learn(db, user, article, signal, previous_feedback=previous)
        await db.commit()
    return {"ok": True, "article_id": body.article_id, "feedback": value}
