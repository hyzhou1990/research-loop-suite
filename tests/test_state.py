import json
from scripts.state import default_state, load_state, save_state


def test_default_state_has_required_fields():
    s = default_state("lit")
    assert s == {
        "watcher_id": "lit", "iteration": 0, "seen_keys": [],
        "empty_streak": 0, "last_hash": None, "cursor": None, "status": "active",
    }


def test_load_missing_file_returns_default(tmp_path):
    p = tmp_path / "lit.json"
    assert load_state(p, "lit") == default_state("lit")


def test_save_then_load_roundtrips(tmp_path):
    p = tmp_path / "lit.json"
    s = default_state("lit")
    s["iteration"] = 3
    s["seen_keys"] = ["a", "b"]
    save_state(p, s)
    assert json.loads(p.read_text())["iteration"] == 3
    assert load_state(p, "lit") == s


def test_load_corrupt_state_raises(tmp_path):
    import pytest
    p = tmp_path / "bad.json"
    p.write_text('{"watcher_id": "lit"}')  # missing required keys
    with pytest.raises(ValueError):
        load_state(p, "lit")
