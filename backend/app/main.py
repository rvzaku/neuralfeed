import structlog
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.deps import require_user_when_enabled
from app.core.rate_limit import RateLimitMiddleware
from app.core.seed import seed_sources, seed_accounts
from app.api.v1 import auth, feed, sources, feedback, preferences, refresh, search, articles, accounts, stories

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


app = FastAPI(title="NeuralFeed API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

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
    stories.router,
]:
    app.include_router(
        router, prefix="/api/v1", dependencies=[Depends(require_user_when_enabled)]
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
