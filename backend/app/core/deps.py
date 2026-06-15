from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Resolve the bearer token to a User, or None when absent/invalid."""
    from app.services import auth_service
    from app.services.auth_service import AuthError

    if not creds:
        return None
    try:
        payload = auth_service.decode_token(creds.credentials)
    except AuthError:
        return None
    return await auth_service.get_user(db, payload.get("sub", ""))


async def is_guest(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> bool:
    """True when the request carries a valid guest token and guest mode is on.
    Used by read routes to apply read-only / quota-safe behavior."""
    from app.services import auth_service

    if not settings.guest_mode_enabled or not creds:
        return False
    return auth_service.is_guest_token(creds.credentials)


async def require_user_when_enabled(
    user=Depends(get_current_user), guest: bool = Depends(is_guest)
):
    """Gate for /api/v1 routes: enforced only when AUTH_REQUIRED=true, so the
    pre-auth single-user deployment keeps working until the flag is flipped.
    A valid guest token satisfies the gate for reads (writes are blocked by the
    guest_read_only middleware regardless)."""
    if settings.auth_required and user is None and not guest:
        raise HTTPException(status_code=401, detail="authentication required")
    return user
