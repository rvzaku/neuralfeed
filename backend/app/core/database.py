from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def normalize_database_url(url: str) -> str:
    """Accept Postgres URLs as pasted from Neon/Render dashboards.

    - postgres:// or postgresql:// → postgresql+asyncpg://
    - sslmode=require (libpq-only) → ssl=require (asyncpg)
    - drops channel_binding, which asyncpg rejects
    """
    if not url.startswith(("postgres://", "postgresql://", "postgresql+asyncpg://")):
        return url
    parts = urlsplit(url)
    scheme = "postgresql+asyncpg"
    query = []
    for key, value in parse_qsl(parts.query):
        if key == "sslmode":
            query.append(("ssl", value))
        elif key == "channel_binding":
            continue
        else:
            query.append((key, value))
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


_db_url = normalize_database_url(settings.database_url)

engine = create_async_engine(
    _db_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in _db_url else {},
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


# Columns added after a table already exists in prod. create_all() only
# creates missing TABLES, never missing columns, so each additive column is
# applied idempotently here. (Proper alembic-on-deploy lands with Phase 3.2.)
_ADDITIVE_COLUMNS = [
    ("sources", "fetch_attempted_at", "TIMESTAMP"),
    ("articles", "ai_deep_summary", "TEXT"),
    ("articles", "ai_deep_summary_at", "TIMESTAMP"),
    ("articles", "image_url", "TEXT"),  # V6 preview images (hotlinked URL metadata)
]


async def _ensure_additive_columns() -> None:
    from sqlalchemy import text

    # One transaction PER column: on Postgres a failed statement (duplicate
    # column) aborts its whole transaction, which would silently skip every
    # ALTER after the first existing column.
    for table, column, ddl_type in _ADDITIVE_COLUMNS:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
        except Exception:
            pass  # column already exists — expected on every boot after the first


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_additive_columns()
