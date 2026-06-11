"""fetch_with_backoff: retries on 429/503 with Retry-After, raises FetchError after max attempts."""

import httpx
import pytest

from app.fetchers.base import FetchError, fetch_with_backoff


def _transport(responses: list[httpx.Response]):
    """MockTransport that pops one canned response per request."""
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        return queue.pop(0)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_succeeds_first_try():
    client = httpx.AsyncClient(transport=_transport([httpx.Response(200, text="ok")]))
    resp = await fetch_with_backoff("https://example.com", client=client, backoffs=(0, 0))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_retries_on_429_then_succeeds():
    client = httpx.AsyncClient(transport=_transport([
        httpx.Response(429, headers={"Retry-After": "0"}),
        httpx.Response(429),
        httpx.Response(200, text="ok"),
    ]))
    resp = await fetch_with_backoff("https://example.com", client=client, backoffs=(0, 0))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_raises_after_exhausting_attempts():
    client = httpx.AsyncClient(transport=_transport([
        httpx.Response(429), httpx.Response(503), httpx.Response(429),
    ]))
    with pytest.raises(FetchError):
        await fetch_with_backoff("https://example.com", client=client, backoffs=(0, 0))


@pytest.mark.asyncio
async def test_non_retryable_error_raises_immediately():
    client = httpx.AsyncClient(transport=_transport([httpx.Response(404)]))
    with pytest.raises(FetchError):
        await fetch_with_backoff("https://example.com", client=client, backoffs=(0, 0))
