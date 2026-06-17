import json
from pathlib import Path

SEVERITY_ORDER = ["critical", "high", "medium", "low"]


def _existing_keys(path):
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            keys.add(json.loads(line)["dedup_key"])
    return keys


def append_findings(inbox_dir, watcher_id, findings):
    inbox_dir = Path(inbox_dir)
    inbox_dir.mkdir(parents=True, exist_ok=True)
    path = inbox_dir / f"{watcher_id}.jsonl"
    seen = _existing_keys(path)
    with path.open("a", encoding="utf-8") as fh:
        for f in findings:
            if f["dedup_key"] in seen:
                continue
            fh.write(json.dumps(f) + "\n")
            seen.add(f["dedup_key"])
    return path


def _read_all(inbox_dir):
    inbox_dir = Path(inbox_dir)
    out = []
    for path in sorted(inbox_dir.glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def render_digest(inbox_dir):
    findings = _read_all(inbox_dir)
    lines = ["# Research Loop — Inbox Digest", ""]
    for sev in SEVERITY_ORDER:
        group = [f for f in findings if f["severity"] == sev]
        if not group:
            continue
        lines.append(f"## {sev.upper()} ({len(group)})")
        for f in group:
            lines.append(f"- **{f['item']}** ({f['type']}) — {f['why_it_matters']} "
                         f"→ _{f['suggested_action']}_  `{f['dedup_key']}` [{f['status']}]")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    import sys
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python3 -m scripts.inbox <inbox_dir>", file=sys.stderr)
        return 2
    print(render_digest(argv[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
