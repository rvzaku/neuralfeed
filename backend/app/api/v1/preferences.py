import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.user_preference import UserPreference

router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferenceIn(BaseModel):
    value: str  # JSON-encoded string


@router.get("", response_model=dict)
async def get_preferences(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(UserPreference))
    prefs = result.scalars().all()
    out = {}
    for p in prefs:
        try:
            out[p.key] = json.loads(p.value)
        except json.JSONDecodeError:
            out[p.key] = p.value
    return out


@router.put("/{key}", status_code=200)
async def set_preference(key: str, body: PreferenceIn, db: AsyncSession = Depends(get_db)) -> dict:
    existing = await db.get(UserPreference, key)
    if existing:
        existing.value = body.value
    else:
        db.add(UserPreference(key=key, value=body.value))
    await db.commit()
    return {"key": key, "value": body.value}
