"""Per-IP sliding-window rate limiting (in-memory).

Adequate for a single Render instance; swap the store for Redis when the
backend scales horizontally. Limits: auth endpoints get a tight budget
(credential stuffing), other write methods a looser one. Reads are unlimited.
"""

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

_WINDOW = 60.0
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _allow(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > _WINDOW:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # CORS preflight (OPTIONS) is a browser protocol detail, not a real
        # request — never rate-limit it, or a handful of legitimate page loads
        # would exhaust the budget and the browser would block the actual call.
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        is_auth = path.startswith("/api/v1/auth")
        is_write = request.method in _WRITE_METHODS
        if not (is_auth or is_write):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        if is_auth:
            ok = self._allow(f"auth:{ip}", settings.rate_limit_auth_per_minute)
        else:
            ok = self._allow(f"write:{ip}", settings.rate_limit_write_per_minute)
        if not ok:
            return JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded, try again shortly"},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
