import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.seed import seed_sources, seed_accounts
from app.api.v1 import feed, sources, feedback, preferences, refresh, search, articles, accounts

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup_begin")
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_sources(db)
        await seed_accounts(db)
    log.info("startup_complete")
    yield
    log.info("shutdown")


app = FastAPI(title="NeuralFeed API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
