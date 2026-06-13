from app.core import scheduler as sched
from app.core.config import settings


def test_hours_for_clamps_to_refresh_max(monkeypatch):
    monkeypatch.setattr(settings, "refresh_max_hours", 4)
    # Daily/weekly sources are pulled forward to the freshness window (V6)
    assert sched._hours_for("daily") == 4
    assert sched._hours_for("weekly") == 4
    # Already-frequent sources keep their tighter cadence
    assert sched._hours_for("4h") == 4
    assert sched._hours_for("12h") == 4  # clamped down too


def test_hours_for_respects_higher_cap(monkeypatch):
    monkeypatch.setattr(settings, "refresh_max_hours", 12)
    assert sched._hours_for("4h") == 4    # never slower than nominal
    assert sched._hours_for("daily") == 12
    assert sched._hours_for("weekly") == 12
