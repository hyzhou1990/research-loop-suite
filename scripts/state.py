import json
from pathlib import Path

import jsonschema

_STATE_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "shared" / "loop_state.schema.json"


def _state_schema():
    return json.loads(_STATE_SCHEMA_PATH.read_text(encoding="utf-8"))


def default_state(watcher_id):
    return {
        "watcher_id": watcher_id,
        "iteration": 0,
        "seen_keys": [],
        "empty_streak": 0,
        "last_hash": None,
        "cursor": None,
        "status": "active",
    }


def load_state(path, watcher_id):
    path = Path(path)
    if not path.exists():
        return default_state(watcher_id)
    state = json.loads(path.read_text())
    try:
        jsonschema.validate(state, _state_schema())
    except jsonschema.ValidationError as e:
        raise ValueError(f"corrupt state file {path}: {e.message}") from e
    return state


def save_state(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))
