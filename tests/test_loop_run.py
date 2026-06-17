import json
import yaml
from scripts.loop_run import run_once
from scripts.findings import make_finding


def write_spec(tmp_path):
    spec = {
        "id": "lit",
        "cadence": {"mode": "manual"},
        "observe": {"target": "biblio", "how": "fake", "inputs": []},
        "flag": {"dedup_key": "doi"},
        "stop": {"max_iterations": 100, "exit_when": {"empty_iterations": 3}},
    }
    spec_path = tmp_path / "lit.yaml"
    spec_path.write_text(yaml.safe_dump(spec))
    return spec_path


def fake_observer(spec):
    return [make_finding("doi:1", "new_paper", "low", "Paper 1", "w", "read")]


def test_run_once_writes_inbox_and_state(tmp_path):
    spec_path = write_spec(tmp_path)
    project = tmp_path / "proj"
    res = run_once(spec_path, project, observer=fake_observer)
    state = json.loads((project / ".research-loop/state/lit.json").read_text())
    assert state["iteration"] == 1
    inbox = (project / ".research-loop/inbox/lit.jsonl").read_text()
    assert "doi:1" in inbox
    assert res["decision"] == "continue"


def test_run_once_twice_is_idempotent(tmp_path):
    spec_path = write_spec(tmp_path)
    project = tmp_path / "proj"
    run_once(spec_path, project, observer=fake_observer)
    res2 = run_once(spec_path, project, observer=fake_observer)
    inbox_lines = (project / ".research-loop/inbox/lit.jsonl").read_text().strip().splitlines()
    assert len(inbox_lines) == 1  # no duplicate finding appended
    assert res2["new_findings"] == []


def test_pause_writes_blocked_marker(tmp_path):
    spec = {
        "id": "lit", "cadence": {"mode": "manual"},
        "observe": {"target": "x", "how": "fake", "inputs": []},
        "flag": {"dedup_key": "doi"},
        "stop": {"max_iterations": 100, "pause_for_human_when": {"severity_at_least": "high"}},
    }
    spec_path = tmp_path / "lit.yaml"
    spec_path.write_text(yaml.safe_dump(spec))
    project = tmp_path / "proj"

    def obs(spec):
        return [make_finding("doi:9", "retraction", "critical", "Bad", "w", "act")]

    run_once(spec_path, project, observer=obs)
    assert (project / ".research-loop/BLOCKED-lit").exists()


def test_run_once_writes_heartbeat_and_log(tmp_path):
    import json as _json
    spec_path = write_spec(tmp_path)   # existing helper in this file (id: lit, manual)
    project = tmp_path / "proj"
    run_once(spec_path, project, observer=fake_observer)   # existing fake_observer -> 1 finding
    hb = _json.loads((project / ".research-loop" / "last_run" / "lit.json").read_text())
    assert hb["decision"] == "continue"
    assert hb["new"] == 1
    log_line = (project / ".research-loop" / "log" / "lit.jsonl").read_text().strip()
    assert "\"decision\": \"continue\"" in log_line or _json.loads(log_line)["decision"] == "continue"
