import json
from pathlib import Path

SEVERITY_ORDER = ["critical", "high", "medium", "low"]


def append_findings(inbox_dir, watcher_id, findings):
    inbox_dir = Path(inbox_dir)
    inbox_dir.mkdir(parents=True, exist_ok=True)
    path = inbox_dir / f"{watcher_id}.jsonl"
    with path.open("a") as fh:
        for f in findings:
            fh.write(json.dumps(f) + "\n")
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
        lines.append(f"## {sev.upper()}")
        for f in group:
            lines.append(f"- **{f['item']}** ({f['type']}) — {f['why_it_matters']} "
                         f"→ _{f['suggested_action']}_ [{f['status']}]")
        lines.append("")
    return "\n".join(lines)
