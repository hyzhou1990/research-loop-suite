import json
import pytest
from scripts.inbox import append_findings, set_status, _read_all
from scripts.findings import make_finding


def _seed(inbox):
    append_findings(inbox, "lit", [
        make_finding("https://openalex.org/W111", "new_paper", "medium", "Paper One", "w", "a"),
        make_finding("https://openalex.org/W222", "new_paper", "medium", "Paper Two", "w", "a"),
    ])
    append_findings(inbox, "data", [
        make_finding("results.csv:abc123", "artifact_change", "medium", "results.csv", "w", "a"),
    ])


def test_set_status_marks_unique_prefix(tmp_path):
    inbox = tmp_path / ".research-loop" / "inbox"
    _seed(inbox)
    updated = set_status(inbox, "https://openalex.org/W111", "ack")
    assert updated["status"] == "ack"
    assert updated["dedup_key"] == "https://openalex.org/W111"
    # persisted: re-read shows ack; the other lit finding and the data file are untouched
    lit = [f for f in _read_all(inbox) if f["dedup_key"] == "https://openalex.org/W111"]
    assert lit[0]["status"] == "ack"
    others = [f["status"] for f in _read_all(inbox) if f["dedup_key"] != "https://openalex.org/W111"]
    assert others == ["new", "new"]


def test_set_status_short_prefix(tmp_path):
    inbox = tmp_path / ".research-loop" / "inbox"
    _seed(inbox)
    updated = set_status(inbox, "results.csv:abc", "dismissed")
    assert updated["dedup_key"] == "results.csv:abc123"
    assert updated["status"] == "dismissed"


def test_set_status_no_match_raises(tmp_path):
    inbox = tmp_path / ".research-loop" / "inbox"
    _seed(inbox)
    with pytest.raises(ValueError):
        set_status(inbox, "nonexistent", "ack")


def test_set_status_ambiguous_raises(tmp_path):
    inbox = tmp_path / ".research-loop" / "inbox"
    _seed(inbox)
    with pytest.raises(ValueError):
        set_status(inbox, "https://openalex.org/W", "ack")  # matches W111 and W222


def test_set_status_invalid_status_raises(tmp_path):
    inbox = tmp_path / ".research-loop" / "inbox"
    _seed(inbox)
    with pytest.raises(ValueError):
        set_status(inbox, "results.csv:abc", "bogus")


def test_set_status_rewrite_keeps_valid_jsonl(tmp_path):
    inbox = tmp_path / ".research-loop" / "inbox"
    _seed(inbox)
    set_status(inbox, "https://openalex.org/W222", "actioned")
    lit_path = inbox / "lit.jsonl"
    lines = [json.loads(l) for l in lit_path.read_text().splitlines() if l.strip()]
    assert len(lines) == 2  # both lit findings still present
    by_key = {f["dedup_key"]: f["status"] for f in lines}
    assert by_key["https://openalex.org/W222"] == "actioned"
    assert by_key["https://openalex.org/W111"] == "new"
    # no leftover temp files in the inbox dir
    assert sorted(p.name for p in inbox.iterdir()) == ["data.jsonl", "lit.jsonl"]
