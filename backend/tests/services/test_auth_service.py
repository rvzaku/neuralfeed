import pytest

from app.services import auth_service
from app.services.auth_service import AuthError

pytestmark = pytest.mark.asyncio


def test_hash_and_verify_roundtrip():
    stored = auth_service.hash_password("hunter22!")
    assert stored.startswith("pbkdf2$")
    assert auth_service.verify_password("hunter22!", stored)
    assert not auth_service.verify_password("wrong", stored)


def test_verify_rejects_malformed_hash():
    assert not auth_service.verify_password("x", "not-a-hash")


async def test_register_and_authenticate(db):
    user = await auth_service.register(db, "Me@Example.COM", "password1")
    assert user.email == "me@example.com"

    same = await auth_service.authenticate(db, "me@example.com", "password1")
    assert same.id == user.id

    with pytest.raises(AuthError):
        await auth_service.authenticate(db, "me@example.com", "nope-nope")


async def test_register_rejects_duplicate_and_weak(db):
    await auth_service.register(db, "dup@example.com", "password1")
    with pytest.raises(AuthError):
        await auth_service.register(db, "dup@example.com", "password2")
    with pytest.raises(AuthError):
        await auth_service.register(db, "new@example.com", "short")
    with pytest.raises(AuthError):
        await auth_service.register(db, "not-an-email", "password1")


async def test_token_roundtrip(db):
    user = await auth_service.register(db, "tok@example.com", "password1")
    token = auth_service.create_token(user)
    payload = auth_service.decode_token(token)
    assert payload["sub"] == user.id

    with pytest.raises(AuthError):
        auth_service.decode_token(token + "tampered")
