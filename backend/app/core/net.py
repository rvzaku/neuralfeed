"""SSRF protection for outbound fetches of untrusted URLs.

NeuralFeed summarizes article pages whose URLs come from RSS feeds — untrusted
input. Without a guard, a malicious feed entry pointing at `http://localhost`,
a private 10.x host, or the cloud metadata endpoint (169.254.169.254) would let
the server fetch internal resources on the attacker's behalf. This module
rejects any URL whose host resolves to a non-public IP, and — via an httpx
request hook — re-checks every redirect hop, since a public URL can 30x into a
private one.
"""

import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

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


def safe_client(**kwargs) -> httpx.AsyncClient:
    """An httpx.AsyncClient that validates every request (incl. redirects)
    against the public-host policy. Pass the same kwargs as AsyncClient."""
    hooks = kwargs.pop("event_hooks", {})
    request_hooks = list(hooks.get("request", []))
    request_hooks.append(_request_hook)
    hooks["request"] = request_hooks
    return httpx.AsyncClient(event_hooks=hooks, **kwargs)
