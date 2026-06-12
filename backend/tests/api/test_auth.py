import pytest

from app.core.config import settings

pytestmark = pytest.mark.asyncio


async def test_register_login_me_flow(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "flow@example.com", "password": "password1"},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "flow@example.com", "password": "password1"},
    )
    assert resp.status_code == 200

    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "flow@example.com"


async def test_login_bad_password_401(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bad@example.com", "password": "password1"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "bad@example.com", "password": "wrong-pass"},
    )
    assert resp.status_code == 401


async def test_me_without_token_401(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_feed_open_when_auth_not_required(client):
    resp = await client.get("/api/v1/feed?limit=1")
    assert resp.status_code == 200


async def test_feed_gated_when_auth_required(client, monkeypatch):
    monkeypatch.setattr(settings, "auth_required", True)
    resp = await client.get("/api/v1/feed?limit=1")
    assert resp.status_code == 401

    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "gate@example.com", "password": "password1"},
    )
    token = reg.json()["access_token"]
    resp = await client.get(
        "/api/v1/feed?limit=1", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
