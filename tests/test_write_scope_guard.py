import json
from scripts.write_scope_guard import decide


def test_allows_write_inside_runtime():
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
