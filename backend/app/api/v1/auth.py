from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services import auth_service
from app.services.auth_service import AuthError

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str


class UserOut(BaseModel):
    id: str
    email: str


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: Credentials, db: AsyncSession = Depends(get_db)) -> TokenOut:
    try:
        user = await auth_service.register(db, body.email, body.password)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TokenOut(access_token=auth_service.create_token(user), email=user.email)


@router.post("/login", response_model=TokenOut)
async def login(body: Credentials, db: AsyncSession = Depends(get_db)) -> TokenOut:
    try:
        user = await auth_service.authenticate(db, body.email, body.password)
    except AuthError:
        raise HTTPException(status_code=401, detail="invalid email or password")
    return TokenOut(access_token=auth_service.create_token(user), email=user.email)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")
    return UserOut(id=user.id, email=user.email)
