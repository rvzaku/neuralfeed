"""Tests for external traction lookup (HN Algolia + Reddit) — V10."""

import httpx
import pytest

from app.services import traction


def _mock_transport(hn_payload=None, reddit_payload=None):
    def handler(request: httpx.Request) -> httpx.Response:
        if "hn.algolia.com" in request.url.host:
            return httpx.Response(200, json=hn_payload or {"hits": []})
        if "reddit.com" in request.url.host:
            return httpx.Response(200, json=reddit_payload or {"data": {"children": []}})
        return httpx.Response(404)
    return httpx.MockTransport(handler)


@pytest.fixture
def patch_client(monkeypatch):
    """Patch httpx.AsyncClient so lookups hit the mock transport."""
    def _apply(hn_payload=None, reddit_payload=None):
        transport = _mock_transport(hn_payload, reddit_payload)
        real_init = httpx.AsyncClient.__init__

        def init(self, *args, **kwargs):
            kwargs["transport"] = transport
            real_init(self, *args, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", init)
    return _apply


@pytest.mark.asyncio
async def test_hacker_news_match_by_exact_url(patch_client):
    patch_client(hn_payload={"hits": [
        {"url": "https://blog.example.com/post", "points": 240, "num_comments": 88, "objectID": "1"},
        {"url": "https://other.com/x", "points": 999, "num_comments": 1, "objectID": "2"},
    ]})
    eng = await traction.fetch_external_engagement("https://blog.example.com/post")
    assert eng["points"] == 240
    assert eng["comments"] == 88
    assert "news.ycombinator.com/item?id=1" in eng["hn_url"]


@pytest.mark.asyncio
async def test_reddit_aggregates_across_submissions(patch_client):
    patch_client(reddit_payload={"data": {"children": [
        {"data": {"score": 120, "num_comments": 30}},
        {"data": {"score": 80, "num_comments": 10}},
    ]}})
    eng = await traction.fetch_external_engagement("https://blog.example.com/post")
    assert eng["upvotes"] == 200
    assert eng["comments"] == 40


@pytest.mark.asyncio
async def test_combined_hn_and_reddit(patch_client):
    patch_client(
        hn_payload={"hits": [{"url": "https://b.com/p", "points": 100, "num_comments": 20, "objectID": "9"}]},
        reddit_payload={"data": {"children": [{"data": {"score": 50, "num_comments": 5}}]}},
    )
    eng = await traction.fetch_external_engagement("https://b.com/p")
    assert eng["points"] == 100
    assert eng["upvotes"] == 50
    assert eng["comments"] == 25  # HN 20 + Reddit 5


@pytest.mark.asyncio
async def test_no_traction_returns_empty(patch_client):
    patch_client()
    assert await traction.fetch_external_engagement("https://nobody.reads/this") == {}


def test_traction_score_weights_hn_above_reddit():
    assert traction._traction_score({"points": 100}) > traction._traction_score({"upvotes": 100})
