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


import json
import subprocess
import sys
from pathlib import Path
from scripts.status import gather, render


def _seed_runtime(tmp_path):
    runtime = tmp_path / ".research-loop"
    lr = runtime / "last_run"
    lr.mkdir(parents=True)
    (lr / "lit.json").write_text(json.dumps(
        {"watcher": "lit", "decision": "continue", "ts": 1000.0, "new": 2, "errors": 0,
         "cadence": {"mode": "self-paced", "every": "1d"}}))
    (lr / "data.json").write_text(json.dumps(
        {"watcher": "data", "decision": "error", "ts": 900.0, "new": 1, "errors": 1,
         "cadence": {"mode": "manual"}}))
    # blocked marker for lit
    (runtime / "BLOCKED-lit").write_text("paused")
    return tmp_path


def test_gather_reads_healths(tmp_path):
    project = _seed_runtime(tmp_path)
    rows = gather(project, now=2000.0)
    by = {r["watcher"]: r for r in rows}
    assert by["lit"]["health"] == "blocked"   # marker present
    assert by["data"]["health"] == "error"
    assert [r["watcher"] for r in rows] == ["data", "lit"]  # sorted


def test_render_contains_watchers(tmp_path):
    project = _seed_runtime(tmp_path)
    rows = gather(project, now=2000.0)
    table = render(rows, now=2000.0)
    assert "lit" in table and "data" in table
    assert "BLOCKED" in table.upper() and "ERROR" in table.upper()


def test_status_cli(tmp_path):
    project = _seed_runtime(tmp_path)
    proc = subprocess.run([sys.executable, "-m", "scripts.status", str(project)],
                          capture_output=True, text=True, cwd=str(Path.cwd()))
    assert proc.returncode == 0
    assert "lit" in proc.stdout and "data" in proc.stdout


def test_status_cli_no_runs(tmp_path):
    proc = subprocess.run([sys.executable, "-m", "scripts.status", str(tmp_path)],
                          capture_output=True, text=True, cwd=str(Path.cwd()))
    assert proc.returncode == 0
    assert "no runs recorded" in proc.stdout.lower()


def test_gather_tolerates_malformed_heartbeat(tmp_path):
    runtime = tmp_path / ".research-loop"
    lr = runtime / "last_run"
    lr.mkdir(parents=True)
    # one good, one malformed (bad JSON), one missing ts
    (lr / "good.json").write_text(json.dumps(
        {"watcher": "good", "decision": "continue", "ts": 1000.0,
         "cadence": {"mode": "manual"}}))
    (lr / "broken.json").write_text("{ not json")
    (lr / "nots.json").write_text(json.dumps({"watcher": "nots", "decision": "continue"}))
    rows = gather(tmp_path, now=2000.0)
    by = {r["watcher"]: r for r in rows}
    assert by["good"]["health"] == "ok"
    # malformed/incomplete files surface as unknown rather than crashing
    assert by["broken"]["health"] == "unknown"
    assert by["nots"]["health"] == "unknown"
