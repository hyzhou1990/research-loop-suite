import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.write_scope_guard import decide


def test_allows_write_inside_runtime_fallback():
    payload = {"tool_name": "Write", "tool_input": {"file_path": "/proj/.research-loop/inbox/lit.jsonl"}}
    allowed, _ = decide(payload, loop_active=True)
    assert allowed is True


def test_blocks_write_outside_runtime_when_active():
    payload = {"tool_name": "Write", "tool_input": {"file_path": "/proj/manuscript.md"}}
    allowed, reason = decide(payload, loop_active=True)
    assert allowed is False
    assert ".research-loop" in reason


def test_allows_everything_when_loop_inactive():
    payload = {"tool_name": "Write", "tool_input": {"file_path": "/proj/manuscript.md"}}
    allowed, _ = decide(payload, loop_active=False)
    assert allowed is True


def test_ignores_non_write_tools():
    payload = {"tool_name": "Read", "tool_input": {"file_path": "/proj/manuscript.md"}}
    allowed, _ = decide(payload, loop_active=True)
    assert allowed is True


def test_substring_lookalike_is_blocked():
    # the loose substring check used to wrongly ALLOW these
    for p in ["/proj/my.research-loop-notes/secret.md", "/evil/.research-loophole/x.md"]:
        payload = {"tool_name": "Write", "tool_input": {"file_path": p}}
        allowed, _ = decide(payload, loop_active=True)
        assert allowed is False, p


def test_bash_blocked_during_loop():
    payload = {"tool_name": "Bash", "tool_input": {"command": "echo x > /proj/manuscript.md"}}
    allowed, reason = decide(payload, loop_active=True)
    assert allowed is False
    assert "Bash" in reason


def test_containment_against_explicit_runtime_dir():
    runtime = Path("/proj/.research-loop")
    inside = {"tool_name": "Write", "tool_input": {"file_path": "/proj/.research-loop/inbox/lit.jsonl"}}
    other = {"tool_name": "Write", "tool_input": {"file_path": "/other/.research-loop/x.md"}}
    assert decide(inside, loop_active=True, runtime_dir=runtime)[0] is True
    # a DIFFERENT project's runtime dir must be blocked when anchored
    assert decide(other, loop_active=True, runtime_dir=runtime)[0] is False


def test_malformed_stdin_fails_closed_when_active():
    script = str(Path("scripts/write_scope_guard.py").resolve())
    env = dict(os.environ, RESEARCH_LOOP_ACTIVE="1")
    proc = subprocess.run([sys.executable, script], input="{ not json",
                          capture_output=True, text=True, env=env)
    assert proc.returncode == 2


def test_malformed_stdin_allows_when_inactive():
    script = str(Path("scripts/write_scope_guard.py").resolve())
    env = dict(os.environ); env.pop("RESEARCH_LOOP_ACTIVE", None)
    proc = subprocess.run([sys.executable, script], input="{ not json",
                          capture_output=True, text=True, env=env)
    assert proc.returncode == 0
