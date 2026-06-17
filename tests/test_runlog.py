import json
from scripts.runlog import record_run


def test_record_run_writes_log_line_and_heartbeat(tmp_path, capsys):
    runtime = tmp_path / ".research-loop"
    record_run(runtime, "lit", "continue", new_count=3, error_count=0,
               duration_ms=820, cadence={"mode": "self-paced", "every": "1d"}, now=1000.0)

    log_path = runtime / "log" / "lit.jsonl"
    entry = json.loads(log_path.read_text().strip())
    assert entry["watcher"] == "lit"
    assert entry["decision"] == "continue"
    assert entry["new"] == 3
    assert entry["errors"] == 0
    assert entry["ms"] == 820
    assert entry["ts"] == 1000.0
    assert entry["cadence"] == {"mode": "self-paced", "every": "1d"}
    assert entry["error"] is None

    hb = json.loads((runtime / "last_run" / "lit.json").read_text())
    assert hb["decision"] == "continue" and hb["new"] == 3 and hb["ts"] == 1000.0

    err = capsys.readouterr().err
    assert "lit" in err and "continue" in err


def test_record_run_appends_history_but_heartbeat_is_latest(tmp_path):
    runtime = tmp_path / ".research-loop"
    record_run(runtime, "lit", "continue", 1, 0, 10, {"mode": "manual"}, now=1.0)
    record_run(runtime, "lit", "exit", 0, 0, 12, {"mode": "manual"}, now=2.0)

    lines = (runtime / "log" / "lit.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    hb = json.loads((runtime / "last_run" / "lit.json").read_text())
    assert hb["decision"] == "exit" and hb["ts"] == 2.0


def test_record_run_includes_error(tmp_path):
    runtime = tmp_path / ".research-loop"
    record_run(runtime, "lit", "error", 1, 1, 5, {"mode": "manual"}, error="boom", now=1.0)
    entry = json.loads((runtime / "log" / "lit.jsonl").read_text().strip())
    assert entry["decision"] == "error" and entry["errors"] == 1 and entry["error"] == "boom"
