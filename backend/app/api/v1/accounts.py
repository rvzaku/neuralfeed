"""
Watched accounts API — manage Twitter/LinkedIn/YouTube accounts to follow.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.watched_account import WatchedAccount

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountOut(BaseModel):
    id: str
    platform: str
    handle: str
    display_name: str
    source_of_discovery: Optional[str]
    enabled: bool
    added_on: str
    notes: Optional[str]

    model_config = {"from_attributes": True}


class AccountIn(BaseModel):
    platform: str
    handle: str
    display_name: str
    notes: Optional[str] = None


class AccountPatch(BaseModel):
    enabled: Optional[bool] = None
    display_name: Optional[str] = None
    notes: Optional[str] = None


@router.get("", response_model=list[AccountOut])
async def list_accounts(
    platform: Optional[str] = None,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[AccountOut]:
    q = select(WatchedAccount).order_by(WatchedAccount.platform, WatchedAccount.handle)
    if platform:
        q = q.where(WatchedAccount.platform == platform)
    if enabled_only:
        q = q.where(WatchedAccount.enabled == True)
    result = await db.execute(q)
    return [AccountOut.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=AccountOut, status_code=201)
async def add_account(body: AccountIn, db: AsyncSession = Depends(get_db)) -> AccountOut:
    handle = body.handle.lstrip("@").lower()
    account_id = f"{body.platform}:{handle}"
    existing = await db.get(WatchedAccount, account_id)
    if existing:
        raise HTTPException(status_code=409, detail="Account already exists")
    account = WatchedAccount(
        id=account_id,
        platform=body.platform,
        handle=handle,
        display_name=body.display_name,
        source_of_discovery="manual",
        enabled=True,
        added_on=date.today(),
        notes=body.notes,
    )
    db.add(account)
    await db.commit()
    return AccountOut.model_validate(account)


@router.patch("/{account_id:path}", response_model=AccountOut)
async def patch_account(
    account_id: str,
    body: AccountPatch,
    db: AsyncSession = Depends(get_db),
) -> AccountOut:
    account = await db.get(WatchedAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if body.enabled is not None:
        account.enabled = body.enabled
    if body.display_name is not None:
        account.display_name = body.display_name
    if body.notes is not None:
        account.notes = body.notes
    await db.commit()
    return AccountOut.model_validate(account)


@router.delete("/{account_id:path}", status_code=204)
async def delete_account(account_id: str, db: AsyncSession = Depends(get_db)) -> None:
    account = await db.get(WatchedAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(account)
    await db.commit()


@router.post("/discover", status_code=200)
async def run_discovery(db: AsyncSession = Depends(get_db)) -> dict:
    """Trigger account discovery from curated_accounts.json + remote lists."""
    from app.fetchers.account_discovery import discover_accounts
    upserted = await discover_accounts(db)
    return {"ok": True, "upserted": upserted}
