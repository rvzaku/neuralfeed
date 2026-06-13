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


# --- DNS-rebinding pinning: the connect-time guard (_resolve_public_ip /
#     _GuardedBackend) is the authoritative layer beyond the request hook. ---


@pytest.mark.asyncio
async def test_resolve_public_ip_literal_public_passthrough():
    assert await net._resolve_public_ip("93.184.216.34", 443) == "93.184.216.34"


@pytest.mark.asyncio
async def test_resolve_public_ip_literal_private_rejected():
    with pytest.raises(UnsafeURLError):
        await net._resolve_public_ip("10.0.0.1", 80)
    with pytest.raises(UnsafeURLError):
        await net._resolve_public_ip("169.254.169.254", 80)


@pytest.mark.asyncio
async def test_resolve_public_ip_hostname_returns_resolved_ip(monkeypatch):
    async def fake_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
    monkeypatch.setattr(net.asyncio.get_event_loop(), "getaddrinfo", fake_getaddrinfo)
    assert await net._resolve_public_ip("example.com", 443) == "93.184.216.34"


@pytest.mark.asyncio
async def test_resolve_public_ip_rejects_private_and_mixed(monkeypatch):
    async def private(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", port))]
    monkeypatch.setattr(net.asyncio.get_event_loop(), "getaddrinfo", private)
    with pytest.raises(UnsafeURLError):
        await net._resolve_public_ip("evil.test", 80)

    async def mixed(host, port, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", port)),
        ]
    monkeypatch.setattr(net.asyncio.get_event_loop(), "getaddrinfo", mixed)
    with pytest.raises(UnsafeURLError):
        await net._resolve_public_ip("rebind.test", 80)


@pytest.mark.asyncio
async def test_guarded_backend_pins_resolved_ip(monkeypatch):
    """The connect MUST target the resolved IP, not the hostname — this is what
    defeats rebinding: even if a hook-time lookup returned a public IP, the
    socket only ever connects to an IP that was just re-validated here."""
    from unittest.mock import AsyncMock

    async def fake_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
    monkeypatch.setattr(net.asyncio.get_event_loop(), "getaddrinfo", fake_getaddrinfo)

    inner = AsyncMock()
    backend = net._GuardedBackend(inner)
    await backend.connect_tcp("example.com", 443)

    inner.connect_tcp.assert_awaited_once()
    connected_host = inner.connect_tcp.await_args.args[0]
    assert connected_host == "93.184.216.34", "must connect to the validated IP, not the name"


@pytest.mark.asyncio
async def test_guarded_backend_blocks_private_connect(monkeypatch):
    from unittest.mock import AsyncMock

    async def fake_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]
    monkeypatch.setattr(net.asyncio.get_event_loop(), "getaddrinfo", fake_getaddrinfo)

    inner = AsyncMock()
    backend = net._GuardedBackend(inner)
    with pytest.raises(UnsafeURLError):
        await backend.connect_tcp("sneaky.test", 80)
    inner.connect_tcp.assert_not_awaited()


@pytest.mark.asyncio
async def test_guarded_backend_refuses_unix_socket():
    from unittest.mock import AsyncMock
    backend = net._GuardedBackend(AsyncMock())
    with pytest.raises(UnsafeURLError):
        await backend.connect_unix_socket("/var/run/x.sock")


def test_safe_client_uses_guarded_transport():
    client = net.safe_client(timeout=10)
    transport = client._transport
    assert isinstance(transport, net._GuardedTransport)
    assert isinstance(transport._pool._network_backend, net._GuardedBackend)
