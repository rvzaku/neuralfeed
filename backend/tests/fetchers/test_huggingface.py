import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# HuggingFace API already filters by pipeline_tag=text-generation server-side.
# All items returned by the API are text-generation; trending_score = downloads / 1000.
HF_RESPONSE = [
    {"id": "org/model-a", "modelId": "org/model-a", "pipeline_tag": "text-generation",
     "lastModified": "2024-01-01T10:00:00.000Z", "likes": 50, "downloads": 2000},
    {"id": "org/model-c", "modelId": "org/model-c", "pipeline_tag": "text-generation",
     "lastModified": "2024-01-01T08:00:00.000Z", "likes": 30, "downloads": 500},
]


@pytest.mark.asyncio
async def test_huggingface_parses_items():
    from app.fetchers.huggingface import HuggingFaceFetcher

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=HF_RESPONSE)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await HuggingFaceFetcher().fetch()

    assert result.ok
    assert len(result.items) == 2
    assert result.items[0]["url"] == "https://huggingface.co/org/model-a"


@pytest.mark.asyncio
async def test_huggingface_empty_response():
    from app.fetchers.huggingface import HuggingFaceFetcher

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=[])

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await HuggingFaceFetcher().fetch()

    assert result.ok
    assert result.items == []


@pytest.mark.asyncio
async def test_huggingface_http_error():
    from app.fetchers.huggingface import HuggingFaceFetcher

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("API error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await HuggingFaceFetcher().fetch()

    assert not result.ok
    assert result.error is not None


@pytest.mark.asyncio
async def test_huggingface_trending_score_from_downloads():
    from app.fetchers.huggingface import HuggingFaceFetcher

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    # downloads=2000 → trending_score = 2000/1000 = 2.0
    mock_response.json = MagicMock(return_value=[HF_RESPONSE[0]])

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await HuggingFaceFetcher().fetch()

    assert result.ok
    assert result.items[0]["trending_score"] == 2.0
