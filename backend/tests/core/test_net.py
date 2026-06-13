"""SSRF guard tests (v0.3.4)."""

import socket

import pytest

from app.core import net
from app.core.net import UnsafeURLError, _ip_is_public, assert_public_url


def test_ip_is_public_classification():
    assert _ip_is_public("8.8.8.8") is True
    assert _ip_is_public("1.1.1.1") is True
    assert _ip_is_public("127.0.0.1") is False        # loopback
    assert _ip_is_public("10.0.0.5") is False          # private
    assert _ip_is_public("192.168.1.1") is False       # private
    assert _ip_is_public("169.254.169.254") is False   # cloud metadata
    assert _ip_is_public("::1") is False               # ipv6 loopback
    assert _ip_is_public("not-an-ip") is False


@pytest.mark.asyncio
async def test_rejects_non_http_scheme():
    with pytest.raises(UnsafeURLError):
        await assert_public_url("file:///etc/passwd")
    with pytest.raises(UnsafeURLError):
        await assert_public_url("ftp://example.com/x")


@pytest.mark.asyncio
async def test_rejects_private_resolution(monkeypatch):
    async def fake_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", port))]
    monkeypatch.setattr(net.asyncio.get_event_loop(), "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeURLError):
        await assert_public_url("http://metadata.evil.test/latest")


@pytest.mark.asyncio
async def test_allows_public_resolution(monkeypatch):
    async def fake_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
    monkeypatch.setattr(net.asyncio.get_event_loop(), "getaddrinfo", fake_getaddrinfo)
    await assert_public_url("https://example.com/article")  # no raise


@pytest.mark.asyncio
async def test_mixed_resolution_rejected_if_any_private(monkeypatch):
    # A host resolving to both a public and a private IP must be rejected —
    # DNS rebinding defense.
    async def fake_getaddrinfo(host, port, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", port)),
        ]
    monkeypatch.setattr(net.asyncio.get_event_loop(), "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeURLError):
        await assert_public_url("http://rebind.test/x")
