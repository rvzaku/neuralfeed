"""Per-user article state: upsert + overlay helpers.

Authenticated requests read/write UserArticleState; anonymous requests keep
using the legacy global columns on Article, so AUTH_REQUIRED=false deploys
behave exactly as before.
"""

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.user_article_state import UserArticleState


async def upsert_state(
    db: AsyncSession,
    user_id: str,
    article_id: str,
    *,
    is_read: Optional[bool] = None,
    is_bookmarked: Optional[bool] = None,
    feedback: Optional[int] = ...,  # sentinel: None is a meaningful value
) -> UserArticleState:
    state = await db.get(UserArticleState, (user_id, article_id))
    if not state:
        state = UserArticleState(user_id=user_id, article_id=article_id)
        db.add(state)
    if is_read is not None:
        state.is_read = is_read
    if is_bookmarked is not None:
        state.is_bookmarked = is_bookmarked
    if feedback is not ...:
        state.feedback = feedback
    state.updated_at = utcnow()
    await db.commit()
    return state


async def mark_seen(db: AsyncSession, user_id: str, article_ids: Iterable[str]) -> int:
    """Batch-mark articles as seen (impression). One SELECT + in-transaction
    upserts, so a whole screen's worth of impressions costs a single round of
    queries. Idempotent: already-seen rows are left untouched."""
    ids = list(dict.fromkeys(article_ids))  # dedupe, preserve order
    if not ids:
        return 0
    existing = await db.execute(
        select(UserArticleState).where(
            UserArticleState.user_id == user_id,
            UserArticleState.article_id.in_(ids),
        )
    )
    by_id = {s.article_id: s for s in existing.scalars().all()}
    now = utcnow()
    for aid in ids:
        state = by_id.get(aid)
        if state is None:
            db.add(UserArticleState(
                user_id=user_id, article_id=aid, is_seen=True, seen_at=now, updated_at=now,
            ))
        elif not state.is_seen:
            state.is_seen = True
            state.seen_at = now
            state.updated_at = now
    await db.commit()
    return len(ids)


async def state_map(
    db: AsyncSession, user_id: str, article_ids: Iterable[str]
) -> dict[str, UserArticleState]:
    ids = list(article_ids)
    if not ids:
        return {}
    result = await db.execute(
        select(UserArticleState).where(
            UserArticleState.user_id == user_id,
            UserArticleState.article_id.in_(ids),
        )
    )
    return {s.article_id: s for s in result.scalars().all()}


def overlay_model(article_out, state: Optional[UserArticleState]):
    """Replace the global flags on an ArticleOut with the user's own, in place.

    Mutating the existing model avoids a model_dump()+model_validate() round-trip
    per item — meaningful on the feed page loop, harmless on single-item routes."""
    article_out.is_read = state.is_read if state else False
    article_out.is_bookmarked = state.is_bookmarked if state else False
    article_out.feedback = state.feedback if state else None
    return article_out
