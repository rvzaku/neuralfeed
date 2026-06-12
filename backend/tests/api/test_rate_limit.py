from app.core.rate_limit import RateLimitMiddleware


def test_sliding_window_allows_then_blocks():
    mw = RateLimitMiddleware(lambda scope, receive, send: None)
    key = "auth:1.2.3.4"
    assert all(mw._allow(key, 3) for _ in range(3))
    assert not mw._allow(key, 3)
    # A different key has its own budget
    assert mw._allow("auth:5.6.7.8", 3)


def test_window_expiry(monkeypatch):
    import app.core.rate_limit as rl

    now = [1000.0]
    monkeypatch.setattr(rl.time, "monotonic", lambda: now[0])
    mw = RateLimitMiddleware(lambda scope, receive, send: None)
    assert mw._allow("k", 1)
    assert not mw._allow("k", 1)
    now[0] += 61
    assert mw._allow("k", 1)
