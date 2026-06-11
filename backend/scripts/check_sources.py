"""Run every registered fetcher once and report health.

Usage:  uv run python scripts/check_sources.py [source_id ...]
Network access required. Does not write to the database.
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.fetchers.registry import FETCHER_MAP  # noqa: E402


async def check_one(source_id: str) -> tuple[str, str, int, float, str]:
    factory = FETCHER_MAP[source_id]
    start = time.monotonic()
    try:
        result = await factory().fetch()
        elapsed = time.monotonic() - start
        if result.ok:
            status = "OK" if result.items else "EMPTY"
            return (source_id, status, len(result.items), elapsed, "")
        return (source_id, "ERROR", 0, elapsed, result.error or "unknown error")
    except Exception as exc:
        return (source_id, "CRASH", 0, time.monotonic() - start, str(exc))


async def main() -> int:
    ids = sys.argv[1:] or sorted(FETCHER_MAP)
    unknown = [i for i in ids if i not in FETCHER_MAP]
    if unknown:
        print(f"unknown source ids: {unknown}")
        return 2

    sem = asyncio.Semaphore(5)

    async def bounded(sid: str):
        async with sem:
            return await check_one(sid)

    results = await asyncio.gather(*[bounded(i) for i in ids])

    width = max(len(r[0]) for r in results)
    failures = 0
    for source_id, status, count, elapsed, error in sorted(results):
        mark = {"OK": "✓", "EMPTY": "~", "ERROR": "✗", "CRASH": "✗"}[status]
        line = f"{mark} {source_id:<{width}}  {status:<6} items={count:<4} {elapsed:5.1f}s"
        if error:
            line += f"  {error[:120]}"
        print(line)
        if status in ("ERROR", "CRASH"):
            failures += 1

    print(f"\n{len(results) - failures}/{len(results)} sources healthy")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
