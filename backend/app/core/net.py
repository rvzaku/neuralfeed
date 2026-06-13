"""SSRF protection for outbound fetches of untrusted URLs.

NeuralFeed summarizes article pages whose URLs come from RSS feeds — untrusted
input. Without a guard, a malicious feed entry pointing at `http://localhost`,
a private 10.x host, or the cloud metadata endpoint (169.254.169.254) would let
the server fetch internal resources on the attacker's behalf.

Defense in depth, two layers:

1. A request hook (`_request_hook`) rejects any non-http(s) scheme and any host
   that resolves to a non-public IP — on the initial request AND every redirect
   hop, since a public URL can 30x into a private one. Fast, early rejection.

2. The authoritative guard against DNS rebinding: a custom network backend
   (`_GuardedBackend`) resolves the host, validates the resolved IP is public,
   and connects the TCP socket to *that pinned IP*. Without this, httpx would
   resolve DNS a second time at connect time — a TOCTOU window where an
   attacker-controlled resolver returns a public IP to the hook's check and a
   private IP to the real connection. Because httpcore still performs TLS with
   the original hostname as SNI/cert name, certificate validation is unaffected.
"""

import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

import httpcore
import httpx


class UnsafeURLError(Exception):
    """The URL's scheme or resolved address is not a public HTTP target."""


def _ip_is_public(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    # Block loopback, private, link-local (incl. 169.254 metadata), reserved,
    # multicast, and unspecified ranges.
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


async def assert_public_url(url: str) -> None:
    """Raise UnsafeURLError unless `url` is http(s) and its host resolves only
    to public IP addresses."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise UnsafeURLError(f"scheme not allowed: {parts.scheme!r}")
    host = parts.hostname
    if not host:
        raise UnsafeURLError("missing host")

    try:
        infos = await asyncio.get_event_loop().getaddrinfo(
            host, parts.port or (443 if parts.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as e:
        raise UnsafeURLError(f"dns resolution failed: {e}")

    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise UnsafeURLError("host resolved to no addresses")
    for ip in addresses:
        if not _ip_is_public(ip):
            raise UnsafeURLError(f"host resolves to non-public address: {ip}")


async def _request_hook(request: httpx.Request) -> None:
    # Fires for the initial request AND every redirect hop, so a public→private
    # redirect is caught before the connection is made.
    await assert_public_url(str(request.url))


async def _resolve_public_ip(host: str, port: int) -> str:
    """Resolve `host` and return ONE validated public IP to connect to.

    Rejects if the host is (or resolves to) any non-public address. Returning a
    concrete IP from this single resolution is what pins the connection — the
    caller connects to this exact IP, so there is no second DNS lookup to
    rebind. A host resolving to a mix of public and private addresses is
    rejected outright (a classic rebinding setup)."""
    try:
        ipaddress.ip_address(host)
        is_literal = True
    except ValueError:
        is_literal = False

    if is_literal:
        if not _ip_is_public(host):
            raise UnsafeURLError(f"host is a non-public address: {host}")
        return host

    try:
        infos = await asyncio.get_event_loop().getaddrinfo(
            host, port, type=socket.SOCK_STREAM
        )
    except socket.gaierror as e:
        raise UnsafeURLError(f"dns resolution failed: {e}")

    addresses = sorted({info[4][0] for info in infos})
    if not addresses:
        raise UnsafeURLError("host resolved to no addresses")
    for ip in addresses:
        if not _ip_is_public(ip):
            raise UnsafeURLError(f"host resolves to non-public address: {ip}")
    return addresses[0]


class _GuardedBackend(httpcore.AsyncNetworkBackend):
    """Wraps the default network backend so every TCP connection goes to a
    freshly-validated public IP, closing the DNS-rebinding TOCTOU. Unix-socket
    connections are refused entirely (no legitimate use for outbound fetches)."""

    def __init__(self, inner: httpcore.AsyncNetworkBackend):
        self._inner = inner

    async def connect_tcp(
        self, host, port, timeout=None, local_address=None, socket_options=None
    ):
        ip = await _resolve_public_ip(host, port)
        return await self._inner.connect_tcp(
            ip, port, timeout=timeout,
            local_address=local_address, socket_options=socket_options,
        )

    async def connect_unix_socket(
        self, path, timeout=None, local_address=None, socket_options=None
    ):
        raise UnsafeURLError("unix-socket connections are not allowed")

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


class _GuardedTransport(httpx.AsyncHTTPTransport):
    """An httpx transport whose connection pool resolves+pins public IPs."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Wrap whatever backend httpx/httpcore selected (asyncio/trio).
        self._pool._network_backend = _GuardedBackend(self._pool._network_backend)


def safe_client(**kwargs) -> httpx.AsyncClient:
    """An httpx.AsyncClient that (a) validates every request URL incl. redirects
    against the public-host policy, and (b) pins the TCP connection to a
    validated public IP so a rebinding resolver can't slip a private address in
    at connect time. Pass the same kwargs as AsyncClient."""
    hooks = kwargs.pop("event_hooks", {})
    request_hooks = list(hooks.get("request", []))
    request_hooks.append(_request_hook)
    hooks["request"] = request_hooks
    return httpx.AsyncClient(
        transport=_GuardedTransport(), event_hooks=hooks, **kwargs
    )
