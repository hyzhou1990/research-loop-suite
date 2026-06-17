import fcntl
import os
import yaml
from pathlib import Path

from scripts.loop_run import run_once
from scripts.findings import make_finding


def _write_spec(tmp_path):
    spec = {
        "id": "data",
        "cadence": {"mode": "manual"},
        "observe": {"target": "t", "how": "fake", "inputs": []},
        "flag": {"dedup_key": "k"},
        "stop": {"max_iterations": 100, "exit_when": {"empty_iterations": 3}},
    }
    p = tmp_path / "data.yaml"
    p.write_text(yaml.safe_dump(spec))
    return p


def _fake(spec):
    return [make_finding("k1", "artifact_change", "low", "i", "w", "a")]


def test_run_once_skips_when_locked(tmp_path):
    spec = _write_spec(tmp_path)
    project = tmp_path / "proj"
    lock_dir = project / ".research-loop" / "state"
    lock_dir.mkdir(parents=True)
    fd = os.open(str(lock_dir / "data.lock"), os.O_CREAT | os.O_RDWR)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        res = run_once(spec, project, observer=_fake)
        assert res["decision"] == "skipped"
        assert res["new_findings"] == []
        assert not (project / ".research-loop" / "inbox" / "data.jsonl").exists()
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_crash_before_state_save_does_not_duplicate(tmp_path):
    spec = _write_spec(tmp_path)
    project = tmp_path / "proj"
    run_once(spec, project, observer=_fake)  # inbox: 1 line, state saved
    # simulate a crash where state never persisted: remove the state file
    (project / ".research-loop" / "state" / "data.json").unlink()
    run_once(spec, project, observer=_fake)  # re-observes k1; append must stay idempotent
    lines = (project / ".research-loop" / "inbox" / "data.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
