import pytest
from pathlib import Path
from scripts.specs import load_spec, validate_spec

VALID = {
    "id": "x",
    "cadence": {"mode": "manual"},
    "observe": {"target": "t", "how": "h", "inputs": []},
    "flag": {"dedup_key": "k"},
    "stop": {"max_iterations": 10, "exit_when": {"empty_iterations": 2}},
}


def test_valid_spec_passes():
    assert validate_spec(dict(VALID)) == VALID


def test_missing_required_block_raises():
    bad = dict(VALID); del bad["flag"]
    with pytest.raises(ValueError):
        validate_spec(bad)


def test_bad_cadence_mode_raises():
    bad = {**VALID, "cadence": {"mode": "hourly"}}
    with pytest.raises(ValueError):
        validate_spec(bad)


def test_bad_severity_threshold_raises():
    bad = {**VALID, "stop": {"max_iterations": 10, "pause_for_human_when": {"severity_at_least": "High"}}}
    with pytest.raises(ValueError):
        validate_spec(bad)


def test_load_spec_rejects_non_mapping(tmp_path):
    p = tmp_path / "s.yaml"; p.write_text("- just\n- a list\n")
    with pytest.raises(ValueError):
        load_spec(p)


def test_load_spec_reports_clear_error_message():
    bad = dict(VALID); del bad["flag"]
    import yaml, tempfile, os
    fd, name = tempfile.mkstemp(suffix=".yaml"); os.close(fd)
    Path(name).write_text(yaml.safe_dump(bad))
    try:
        with pytest.raises(ValueError) as ei:
            load_spec(name)
        assert "watch-spec" in str(ei.value)
    finally:
        os.unlink(name)


def test_all_shipped_watchers_validate():
    suite = Path(__file__).resolve().parent.parent
    specs = list((suite / "watchers").glob("*.yaml"))
    assert specs, "no watcher specs found"
    for s in specs:
        load_spec(s)  # must not raise
