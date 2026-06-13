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
from app.api.v1 import auth, feed, sources, feedback, preferences, refresh, search, articles, accounts

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Auth is a Bearer token in the Authorization header, not a cookie, so
    # credentialed CORS is unnecessary; keeping it false avoids the browser
    # CORS pitfall where credentials force an exact (non-wildcard) origin.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1024)

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
]:
    app.include_router(
        router, prefix="/api/v1", dependencies=[Depends(require_user_when_enabled)]
    )


# HEAD included for uptime monitors (UptimeRobot free tier probes with HEAD)
@app.api_route("/health", methods=["GET", "HEAD"])
async def health() -> dict:
    return {"status": "ok"}
