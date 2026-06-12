import pytest

pytestmark = pytest.mark.asyncio

async def test_stories_authed(client):
    r = await client.post("/api/v1/auth/register", json={"email": "st@example.com", "password": "password1"})
    tok = r.json()["access_token"]
    resp = await client.get("/api/v1/stories?days=7&limit=5", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200, resp.text
