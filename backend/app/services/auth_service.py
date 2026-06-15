"""Email/password auth with stdlib PBKDF2 hashing and HS256 JWTs.

Phase 3.1a: single-credential auth gate. Per-user article state arrives in
increment 2; until then every authenticated user shares the same feed state.
"""

import hashlib
import hmac
import os
import re
from datetime import timedelta
from typing import Optional

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.time import utcnow
from app.models.user import User

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PBKDF2_ITERATIONS = 600_000  # OWASP 2023 recommendation for PBKDF2-SHA256


class AuthError(Exception):
    """Invalid credentials, duplicate email, or bad/expired token."""


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "exp": utcnow() + timedelta(minutes=settings.jwt_expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_guest_token() -> str:
    """Short-lived, read-only guest session. Carries role=guest and no user id;
    every mutating request bearing this token is rejected by middleware, and the
    summary route refuses to spend LLM quota for it beyond strict caps."""
    payload = {
        "sub": "guest",
        "role": "guest",
        "exp": utcnow() + timedelta(minutes=settings.guest_token_expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise AuthError(f"invalid token: {e}")


def is_guest_token(token: str) -> bool:
    """True only for a valid, unexpired guest token. Invalid/expired → False."""
    try:
        return decode_token(token).get("role") == "guest"
    except AuthError:
        return False


async def register(db: AsyncSession, email: str, password: str) -> User:
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise AuthError("invalid email address")
    if len(password) < 8:
        raise AuthError("password must be at least 8 characters")
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise AuthError("email already registered")
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email.strip().lower()))
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("invalid email or password")
    return user


async def get_user(db: AsyncSession, user_id: str) -> Optional[User]:
    return await db.get(User, user_id)
