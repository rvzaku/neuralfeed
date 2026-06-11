"""UTC time helpers.

All DateTime columns are TIMESTAMP WITHOUT TIME ZONE, so every value
written to or compared against the DB must be naive UTC. SQLite ignored
the difference; asyncpg/Postgres rejects aware datetimes on naive columns.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (for DB storage/comparison)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt: datetime) -> datetime:
    """Convert any datetime to naive UTC. Naive input is assumed UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
