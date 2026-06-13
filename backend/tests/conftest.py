import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.deps import get_db
from app.main import app
from app.core.seed import seed_sources

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def db(engine):
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        await seed_sources(session)
        yield session


@pytest.fixture(autouse=True)
def _no_rate_limit(monkeypatch):
    # The shared in-memory limiter would couple tests; covered by its own unit tests
    from app.core.config import settings
    monkeypatch.setattr(settings, "rate_limit_enabled", False)


@pytest.fixture(autouse=True)
def _no_feed_cache(monkeypatch):
    # The feed cache is process-global and keyed by filters, not DB contents, so
    # a stray dev Redis could leak one test's ranked order into another. Tests
    # always recompute; the cache has its own unit coverage.
    from app.core.config import settings
    monkeypatch.setattr(settings, "feed_cache_enabled", False)


@pytest.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
