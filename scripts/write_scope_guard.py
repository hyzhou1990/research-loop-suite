import json
import os
import sys
from pathlib import Path

WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}


def _runtime_dir_from_env():
    rt = os.environ.get("RESEARCH_LOOP_RUNTIME")
    return Path(rt).resolve() if rt else None


def _is_within(target, runtime_dir):
    if not target:
        return False
    resolved = Path(target).resolve()
    if runtime_dir is not None:
        return resolved == runtime_dir or runtime_dir in resolved.parents
    # Fallback (no anchor supplied): require a real '.research-loop' path component,
    # not a substring. Cannot distinguish *which* project's runtime dir.
    return ".research-loop" in resolved.parts


def decide(payload, loop_active, runtime_dir=None):
    """Return (allowed, reason). Enforces observe-only during a loop run."""
    if not loop_active:
        return True, ""
    tool = payload.get("tool_name", "")
    if tool == "Bash":
        return False, (
            "Loop run is observe-only: Bash is disabled during a loop iteration because "
            "its writes cannot be reliably scoped. Graduate this to a human Tier-2 action."
        )
    if tool not in WRITE_TOOLS:
        return True, ""
    target = payload.get("tool_input", {}).get("file_path", "")
    if _is_within(target, runtime_dir):
        return True, ""
    return False, (
        "Loop run is observe-only: writes must stay inside .research-loop/. "
        f"Blocked write to {target!r}. Graduate this to a human Tier-2 action instead."
    )


def main():
    loop_active = os.environ.get("RESEARCH_LOOP_ACTIVE") == "1"
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        if loop_active:
            print("write-scope guard: unparseable tool input; blocking (fail-closed).", file=sys.stderr)
            return 2
        return 0
    allowed, reason = decide(payload, loop_active, runtime_dir=_runtime_dir_from_env())
    if allowed:
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
