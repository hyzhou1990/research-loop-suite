import json
import sys
from pathlib import Path

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_interval(s):
    """'30m'/'6h'/'1d'/'2w'/'45s' -> seconds; unknown/empty -> None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    unit = s[-1:]
    if unit not in _UNIT_SECONDS:
        return None
    try:
        value = int(s[:-1])
    except ValueError:
        return None
    return value * _UNIT_SECONDS[unit]


def classify(last_run, now, blocked):
    """Return (health, age_seconds). Precedence: blocked > error > stale > ok."""
    age = now - last_run["ts"]
    if blocked:
        return "blocked", age
    if last_run.get("decision") == "error":
        return "error", age
    cadence = last_run.get("cadence") or {}
    if cadence.get("mode") in ("cron", "self-paced"):
        interval = parse_interval(cadence.get("every"))
        if interval is not None and age > 2 * interval:
            return "stale", age
    return "ok", age


def _human_age(seconds):
    seconds = int(max(0, seconds))
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def gather(project_root, now):
    runtime = Path(project_root) / ".research-loop"
    last_run_dir = runtime / "last_run"
    rows = []
    if not last_run_dir.exists():
        return rows
    for path in sorted(last_run_dir.glob("*.json")):
        last_run = json.loads(path.read_text(encoding="utf-8"))
        watcher = last_run.get("watcher", path.stem)
        blocked = (runtime / f"BLOCKED-{watcher}").exists()
        health, age = classify(last_run, now, blocked)
        rows.append({
            "watcher": watcher,
            "health": health,
            "age_seconds": age,
            "decision": last_run.get("decision", "?"),
        })
    return rows


def render(rows, now):
    if not rows:
        return "no runs recorded yet"
    lines = []
    for r in rows:
        detail = r["decision"]
        lines.append(f"{r['watcher']:<12} {r['health'].upper():<8} "
                     f"{_human_age(r['age_seconds']):<10} {detail}")
    return "\n".join(lines)


def main(argv=None):
    import time
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python3 -m scripts.status <project_root>", file=sys.stderr)
        return 2
    rows = gather(argv[0], now=time.time())
    print(render(rows, now=time.time()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
