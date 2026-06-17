import json
import sys
import time
from pathlib import Path

from scripts.io_utils import atomic_write_text


def record_run(runtime, watcher_id, decision, new_count, error_count,
               duration_ms, cadence, error=None, now=None):
    """Append a structured run-log line, write the heartbeat, echo a human line to stderr."""
    runtime = Path(runtime)
    ts = time.time() if now is None else now
    entry = {
        "ts": ts,
        "watcher": watcher_id,
        "decision": decision,
        "new": new_count,
        "errors": error_count,
        "ms": duration_ms,
        "cadence": cadence or {},
        "error": error,
    }

    log_dir = runtime / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / f"{watcher_id}.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

    # The JSONL history above is the source of truth; the heartbeat is a best-effort
    # latest-state cache (a crash between the two leaves history ahead — acceptable).
    atomic_write_text(runtime / "last_run" / f"{watcher_id}.json", json.dumps(entry, indent=2))

    print(f"{watcher_id}: {decision}, {new_count} new, {error_count} err ({duration_ms}ms)",
          file=sys.stderr)
    return entry
