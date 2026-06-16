import json
from scripts.inbox import append_findings, render_digest
from scripts.findings import make_finding


def test_append_writes_jsonl(tmp_path):
    inbox = tmp_path / "inbox"
    f = make_finding("a", "new_paper", "high", "Smith 2026", "matches RQ", "read")
    path = append_findings(inbox, "lit", [f])
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["dedup_key"] == "a"


def test_append_is_additive(tmp_path):
    inbox = tmp_path / "inbox"
    append_findings(inbox, "lit", [make_finding("a", "t", "low", "i", "w", "x")])
    path = append_findings(inbox, "lit", [make_finding("b", "t", "low", "i", "w", "x")])
    assert len(path.read_text().strip().splitlines()) == 2


def test_render_digest_groups_by_severity(tmp_path):
    inbox = tmp_path / "inbox"
    append_findings(inbox, "lit", [
        make_finding("a", "t", "critical", "Crit item", "w", "x"),
        make_finding("b", "t", "low", "Low item", "w", "x"),
    ])
    md = render_digest(inbox)
    assert "CRITICAL" in md
    assert md.index("Crit item") < md.index("Low item")  # critical listed first
