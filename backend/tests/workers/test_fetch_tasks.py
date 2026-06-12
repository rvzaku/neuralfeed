import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestFetcherMap:
    def test_all_reddit_ids_in_fetcher_map(self):
        from app.fetchers.registry import FETCHER_MAP, _REDDIT_IDS
        for sid in _REDDIT_IDS:
            assert sid in FETCHER_MAP, f"{sid} missing from FETCHER_MAP"

    def test_phase2_sources_in_fetcher_map(self):
        from app.fetchers.registry import FETCHER_MAP
        for sid in ("hf-models", "youtube-ai", "twitter-nitter"):
            assert sid in FETCHER_MAP

    def test_rss_sources_in_fetcher_map(self):
        from app.fetchers.registry import FETCHER_MAP
        from app.fetchers.rss import RSS_SOURCES
        for sid in RSS_SOURCES:
            assert sid in FETCHER_MAP

    def test_worker_module_reexports_registry(self):
        from app.workers.fetch_tasks import FETCHER_MAP as worker_map
        from app.fetchers.registry import FETCHER_MAP
        assert worker_map is FETCHER_MAP


def _mock_db(source=None):
    db = AsyncMock()
    db.get = AsyncMock(return_value=source)
    db.commit = AsyncMock()
    return db


def _mock_source():
    source = MagicMock()
    return source


class TestRunFetch:
    @pytest.mark.asyncio
    async def test_unknown_source_returns_zero_and_records_error(self):
        from app.services.fetch_runner import run_fetch
        source = _mock_source()
        db = _mock_db(source)
        result = await run_fetch("does-not-exist", db)
        assert result == 0
        assert source.last_fetch_status == "error"
        assert "no fetcher" in source.last_fetch_error

    @pytest.mark.asyncio
    async def test_failed_fetch_returns_zero_and_records_error(self):
        from app.fetchers.base import FetchResult
        from app.fetchers import registry
        from app.services import fetch_runner

        mock_fetcher = MagicMock()
        mock_fetcher.fetch = AsyncMock(return_value=FetchResult(source_id="test-src", error="timeout"))
        source = _mock_source()
        db = _mock_db(source)

        with patch.dict(registry.FETCHER_MAP, {"test-src": lambda: mock_fetcher}):
            result = await fetch_runner.run_fetch("test-src", db)

        assert result == 0
        assert source.last_fetch_status == "error"
        assert source.last_fetch_error == "timeout"

    @pytest.mark.asyncio
    async def test_crashing_fetcher_is_contained(self):
        from app.fetchers import registry
        from app.services import fetch_runner

        mock_fetcher = MagicMock()
        mock_fetcher.fetch = AsyncMock(side_effect=RuntimeError("boom"))
        source = _mock_source()
        db = _mock_db(source)

        with patch.dict(registry.FETCHER_MAP, {"test-src": lambda: mock_fetcher}):
            result = await fetch_runner.run_fetch("test-src", db)

        assert result == 0
        assert source.last_fetch_status == "error"
        assert "boom" in source.last_fetch_error

    @pytest.mark.asyncio
    async def test_successful_fetch_calls_ingest_and_records_ok(self):
        from app.fetchers.base import FetchResult
        from app.fetchers import registry
        from app.services import fetch_runner

        items = [{"title": "T", "url": "https://example.com/a", "published_at": None, "trending_score": 0.0}]
        mock_fetcher = MagicMock()
        mock_fetcher.fetch = AsyncMock(return_value=FetchResult(source_id="test-src2", items=items))
        source = _mock_source()
        db = _mock_db(source)

        with patch.dict(registry.FETCHER_MAP, {"test-src2": lambda: mock_fetcher}):
            with patch("app.services.fetch_runner.ingest_items", new=AsyncMock(return_value=1)) as mock_ingest:
                result = await fetch_runner.run_fetch("test-src2", db)

        mock_ingest.assert_called_once()
        assert result == 1
        assert source.last_fetch_status == "ok"
        assert source.last_fetch_error is None
        assert source.last_fetch_count == 1
