import structlog
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.deps import require_user_when_enabled
from app.core.rate_limit import RateLimitMiddleware
from app.core.seed import seed_sources, seed_accounts
from app.api.v1 import auth, feed, sources, feedback, preferences, refresh, search, articles, accounts, topics, digest

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup_begin")
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_sources(db)
        await seed_accounts(db)
    if settings.scheduler_enabled:
        from app.core.scheduler import start_scheduler
        await start_scheduler()
    log.info("startup_complete")
    yield
    if settings.scheduler_enabled:
        from app.core.scheduler import stop_scheduler
        stop_scheduler()
    log.info("shutdown")


if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

if settings.auth_required and settings.jwt_secret == "dev-secret-change-me":
    raise RuntimeError("AUTH_REQUIRED=true with the default JWT secret — set JWT_SECRET")

app = FastAPI(title="NeuralFeed API", version="0.2.0", lifespan=lifespan)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store"
    return response


_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def guest_read_only(request, call_next):
    """Single choke point: a guest token may never perform a mutating request.
    Covers every write route — current and future — so read-only is enforced
    server-side, not just hidden in the UI. No-op unless guest mode is on."""
    if settings.guest_mode_enabled and request.method in _MUTATING_METHODS:
        from fastapi.responses import JSONResponse
        from app.services import auth_service

        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer ") and auth_service.is_guest_token(auth[7:]):
            return JSONResponse(
                status_code=403,
                content={"detail": "Guests are read-only — sign in to make changes."},
            )
    return await call_next(request)

# Middleware ordering matters: Starlette runs the LAST-added middleware
# OUTERMOST. CORS must be the outermost layer so that EVERY response — including
# error responses produced by inner middleware (a 429 from the rate limiter, a
# 403 from guest_read_only) and CORS preflight (OPTIONS) — carries the
# Access-Control-Allow-Origin header. If CORS were inner, the browser would
# block those responses with an opaque network error even though the server
# answered correctly (the classic "works in curl, fails in the browser" trap).
# Hence: add GZip and RateLimit first (inner), then CORS last (outer).
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Optional regex (e.g. Vercel preview deploys) — off unless configured.
    allow_origin_regex=settings.cors_origin_regex or None,
    # Auth is a Bearer token in the Authorization header, not a cookie, so
    # credentialed CORS is unnecessary; keeping it false avoids the browser
    # CORS pitfall where credentials force an exact (non-wildcard) origin.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Auth endpoints are never gated; everything else requires a user once
# AUTH_REQUIRED=true (no-op until then — see require_user_when_enabled).
app.include_router(auth.router, prefix="/api/v1")

for router in [
    feed.router,
    sources.router,
    feedback.router,
    preferences.router,
    refresh.router,
    search.router,
    articles.router,
    accounts.router,
    topics.router,
    digest.router,
]:
    app.include_router(
        router, prefix="/api/v1", dependencies=[Depends(require_user_when_enabled)]
    )


# HEAD included for uptime monitors (UptimeRobot free tier probes with HEAD)
@app.api_route("/health", methods=["GET", "HEAD"])
async def health() -> dict:
    return {"status": "ok"}
