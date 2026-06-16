import json
from pathlib import Path


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
    return json.loads(path.read_text())


def save_state(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))
