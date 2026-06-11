import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.fetchers.hf_spaces import HFSpacesFetcher

SAMPLE_SPACES = [
    {"id": "black-forest-labs/flux-pro", "likes": 4200, "lastModified": "2026-06-10T08:00:00.000Z",
     "cardData": {"title": "FLUX Pro"}},
    {"id": "someuser/demo", "likes": 12, "lastModified": None, "cardData": {}},
    {"id": "", "likes": 0},  # malformed — must be skipped
]


def _mock_client(json_data):
    resp = MagicMock()
    resp.json = MagicMock(return_value=json_data)
    resp.raise_for_status = MagicMock()
    client = AsyncMock()
    client.get = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.mark.asyncio
async def test_hf_spaces_parses_and_skips_malformed():
    with patch("app.fetchers.hf_spaces.httpx.AsyncClient", return_value=_mock_client(SAMPLE_SPACES)):
        result = await HFSpacesFetcher().fetch()

    assert result.ok
    assert len(result.items) == 2
    top = result.items[0]
    assert top["title"] == "FLUX Pro"
    assert top["url"] == "https://huggingface.co/spaces/black-forest-labs/flux-pro"
    assert top["author"] == "black-forest-labs"
    assert top["trending_score"] == 4200.0
    # item without lastModified still gets a published_at
    assert result.items[1]["published_at"] is not None


@pytest.mark.asyncio
async def test_hf_spaces_error_returns_failed_result():
    client = AsyncMock()
    client.get = AsyncMock(side_effect=Exception("api down"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    with patch("app.fetchers.hf_spaces.httpx.AsyncClient", return_value=client):
        result = await HFSpacesFetcher().fetch()
    assert not result.ok
