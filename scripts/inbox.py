import json
import os
import sys
import tempfile
from pathlib import Path

from scripts.locking import watcher_lock, LoopBusy

SEVERITY_ORDER = ["critical", "high", "medium", "low"]
VALID_STATUS = {"ack", "dismissed", "actioned"}


def _existing_keys(path):
    # Re-reads the whole inbox file per append: O(n) each call. Fine at loop cadence
    # (few findings/iteration, KB-scale files); revisit if a high-frequency watcher
    # grows an inbox to tens of thousands of lines.
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


def render_digest(inbox_dir, show_all=False):
    findings = _read_all(inbox_dir)
    if not show_all:
        findings = [f for f in findings if f.get("status") != "dismissed"]
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


def _atomic_write_lines(path, lines):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def set_status(inbox_dir, dedup_key_prefix, new_status):
    if new_status not in VALID_STATUS:
        raise ValueError(f"invalid status {new_status!r}; expected one of {sorted(VALID_STATUS)}")
    inbox_dir = Path(inbox_dir)

    # find all matches (across every watcher's jsonl) by dedup_key prefix
    matches = []  # (path, line_index, finding)
    files = {}    # path -> list[finding]
    for path in sorted(inbox_dir.glob("*.jsonl")):
        findings = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        files[path] = findings
        for i, f in enumerate(findings):
            if f["dedup_key"].startswith(dedup_key_prefix):
                matches.append((path, i, f))

    if not matches:
        raise ValueError(f"no finding matches prefix {dedup_key_prefix!r}")
    if len(matches) > 1:
        raise ValueError(f"ambiguous prefix {dedup_key_prefix!r} matches {len(matches)} findings")

    path, idx, finding = matches[0]
    watcher_id = path.stem
    runtime = inbox_dir.parent  # the .research-loop dir
    try:
        with watcher_lock(runtime, watcher_id):
            findings = files[path]
            findings[idx]["status"] = new_status
            _atomic_write_lines(path, [json.dumps(f) for f in findings])
    except LoopBusy as e:
        raise RuntimeError(f"watcher {watcher_id!r} is running; try triage again shortly") from e
    return findings[idx]


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(prog="scripts.inbox", description="Research Loop inbox")
    parser.add_argument("inbox_dir")
    parser.add_argument("command", nargs="?", default="digest",
                        choices=["digest", "ack", "dismiss", "actioned"])
    parser.add_argument("key", nargs="?", default=None)
    parser.add_argument("--all", action="store_true", help="include dismissed findings in the digest")
    args = parser.parse_args(argv)

    if args.command == "digest":
        print(render_digest(args.inbox_dir, show_all=args.all))
        return 0

    if not args.key:
        print(f"usage: scripts.inbox <inbox_dir> {args.command} <dedup_key_prefix>", file=sys.stderr)
        return 2
    # CLI verb -> stored status value ("dismiss" command sets status "dismissed")
    status_by_command = {"ack": "ack", "dismiss": "dismissed", "actioned": "actioned"}
    try:
        updated = set_status(args.inbox_dir, args.key, status_by_command[args.command])
    except (ValueError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        return 2
    print(f"{updated['status']}: {updated['item']} ({updated['dedup_key']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
