import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user_preference import UserPreference

router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferenceIn(BaseModel):
    value: str  # JSON-encoded string


@router.get("", response_model=dict)
async def get_preferences(
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
) -> dict:
    prefix = f"u:{user.id}:" if user else ""
    result = await db.execute(select(UserPreference))
    prefs = result.scalars().all()
    out = {}
    for p in prefs:
        if prefix:
            if not p.key.startswith(prefix):
                continue
            key = p.key[len(prefix):]
        else:
            if p.key.startswith("u:"):
                continue
            key = p.key
        try:
            out[key] = json.loads(p.value)
        except json.JSONDecodeError:
            out[key] = p.value
    return out


@router.put("/{key}", status_code=200)
async def set_preference(
    key: str,
    body: PreferenceIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    if user:
        key = f"u:{user.id}:{key}"
    existing = await db.get(UserPreference, key)
    if existing:
        existing.value = body.value
    else:
        db.add(UserPreference(key=key, value=body.value))
    await db.commit()
    return {"key": key.split(":", 2)[-1], "value": body.value}
