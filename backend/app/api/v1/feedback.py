from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.article import Article
from app.models.feedback_log import FeedbackLog
from app.models.source import Source
from app.schemas.feedback import FeedbackIn

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=200)
async def post_feedback(body: FeedbackIn, db: AsyncSession = Depends(get_db)) -> dict:
    article = await db.get(Article, body.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.feedback = body.value if body.value != 0 else None

    db.add(FeedbackLog(
        article_id=body.article_id,
        source_id=article.source_id,
        value=body.value,
        created_at=datetime.now(timezone.utc),
    ))

    await db.commit()

    result = await db.execute(
        select(
            func.count(Article.id).label("total"),
            func.sum((Article.feedback == 1).cast(int)).label("positive"),
        ).where(Article.source_id == article.source_id, Article.feedback != None)
    )
    row = result.one()
    if row.total and row.total > 0:
        source = await db.get(Source, article.source_id)
        if source:
            source.signal_score = round((row.positive or 0) / row.total, 3)
            await db.commit()

    return {"ok": True, "article_id": body.article_id, "feedback": article.feedback}
