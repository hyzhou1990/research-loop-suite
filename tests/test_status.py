import pytest
from scripts.status import parse_interval, classify


def test_parse_interval_units():
    assert parse_interval("45s") == 45
    assert parse_interval("30m") == 1800
    assert parse_interval("6h") == 21600
    assert parse_interval("1d") == 86400
    assert parse_interval("2w") == 1209600


def test_parse_interval_bad_returns_none():
    assert parse_interval("") is None
    assert parse_interval(None) is None
    assert parse_interval("soon") is None


def _lr(decision="continue", ts=1000.0, mode="self-paced", every="1d"):
    return {"decision": decision, "ts": ts, "cadence": {"mode": mode, "every": every}}


def test_classify_ok_recent():
    health, age = classify(_lr(ts=1000.0), now=1100.0, blocked=False)
    assert health == "ok"
    assert age == 100.0


def test_classify_stale_when_overdue():
    # 1d interval, age = 3 days > 2*interval
    health, _ = classify(_lr(ts=0.0, every="1d"), now=3 * 86400, blocked=False)
    assert health == "stale"


def test_classify_manual_never_stale():
    health, _ = classify(_lr(ts=0.0, mode="manual", every=None), now=10 * 86400, blocked=False)
    assert health == "ok"


def test_classify_error_decision():
    health, _ = classify(_lr(decision="error", ts=1000.0), now=1001.0, blocked=False)
    assert health == "error"


def test_classify_blocked_takes_precedence():
    # blocked beats error/stale/ok
    health, _ = classify(_lr(decision="error", ts=0.0), now=10 * 86400, blocked=True)
    assert health == "blocked"
