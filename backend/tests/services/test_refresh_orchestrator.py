"""refresh_orchestrator: batched, error-isolated, resumable full refresh."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.core.time import utcnow
from app.models.source import Source
from app.services import refresh_orchestrator as ro


@pytest.fixture
def session_factory(engine, db):
    """Real per-call sessions, like AsyncSessionLocal in prod (db ensures seed)."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_refreshes_all_enabled_sources(db, session_factory):
    with patch.object(ro, "run_fetch", new=AsyncMock(return_value=1)) as mock_fetch:
        await ro.refresh_all(session_factory=session_factory, concurrency=2)

    db.expire_all()
    enabled = (await db.execute(select(Source).where(Source.enabled == True))).scalars().all()
    fetchable = [s for s in enabled if s.id in ro.FETCHER_MAP]
    called_ids = {c.args[0] for c in mock_fetch.call_args_list}
    assert called_ids == {s.id for s in fetchable}
    # cursor stamped on every attempted source
    assert all(s.fetch_attempted_at is not None for s in fetchable)


@pytest.mark.asyncio
async def test_one_failing_source_does_not_stop_others(db, session_factory):
    calls = []

    async def flaky(source_id, _db):
        calls.append(source_id)
        if len(calls) == 1:
            raise RuntimeError("boom")
        return 1

    with patch.object(ro, "run_fetch", new=flaky):
        await ro.refresh_all(session_factory=session_factory, concurrency=1)

    assert len(calls) > 1  # others still ran


@pytest.mark.asyncio
async def test_least_recently_attempted_go_first(db, session_factory):
    # Mark every source as already attempted except two stragglers
    sources = (await db.execute(select(Source).where(Source.enabled == True))).scalars().all()
    fetchable = [s for s in sources if s.id in ro.FETCHER_MAP]
    stragglers = {fetchable[-1].id, fetchable[-2].id}
    for s in fetchable:
        if s.id not in stragglers:
            s.fetch_attempted_at = utcnow()
    await db.commit()

    order = []

    async def record(source_id, _db):
        order.append(source_id)
        return 0

    with patch.object(ro, "run_fetch", new=record):
        await ro.refresh_all(session_factory=session_factory, concurrency=1)

    assert set(order[:2]) == stragglers  # never-attempted sources first


@pytest.mark.asyncio
async def test_progress_reporting(db, session_factory):
    with patch.object(ro, "run_fetch", new=AsyncMock(return_value=1)):
        await ro.refresh_all(session_factory=session_factory, concurrency=2)
    progress = ro.get_progress()
    assert progress["running"] is False
    assert progress["done"] == progress["total"] > 0
