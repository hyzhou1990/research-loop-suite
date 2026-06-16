from scripts.write_scope_guard import decide


def test_loop_cannot_edit_manuscript():
    # Simulate a loop iteration trying to edit the manuscript (Tier-2 mutation)
    payload = {"tool_name": "Edit", "tool_input": {"file_path": "/proj/sections/intro.md"}}
    allowed, reason = decide(payload, loop_active=True)
    assert allowed is False
    assert "observe-only" in reason


def test_loop_can_write_inbox():
    payload = {"tool_name": "Write", "tool_input": {"file_path": "/proj/.research-loop/inbox/lit.jsonl"}}
    allowed, _ = decide(payload, loop_active=True)
    assert allowed is True
