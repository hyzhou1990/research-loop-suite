import json
import os
import sys

WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}


def decide(payload, loop_active):
    """Return (allowed: bool, reason: str)."""
    if not loop_active:
        return True, ""
    tool = payload.get("tool_name", "")
    if tool not in WRITE_TOOLS:
        return True, ""
    target = payload.get("tool_input", {}).get("file_path", "")
    if ".research-loop" in target:
        return True, ""
    return False, (
        "Loop run is observe-only: writes must stay inside .research-loop/. "
        f"Blocked write to {target}. Graduate this to a human Tier-2 action instead."
    )


def main():
    payload = json.loads(sys.stdin.read() or "{}")
    loop_active = os.environ.get("RESEARCH_LOOP_ACTIVE") == "1"
    allowed, reason = decide(payload, loop_active)
    if allowed:
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
