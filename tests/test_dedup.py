from scripts.loop_engine import dedup_findings
from scripts.findings import make_finding


def _f(key):
    return make_finding(key, "new_paper", "low", key, "w", "a")


def test_dedup_keeps_only_unseen():
    candidates = [_f("a"), _f("b"), _f("c")]
    out = dedup_findings(candidates, ["b"])
    assert [f["dedup_key"] for f in out] == ["a", "c"]


def test_dedup_empty_when_all_seen():
    candidates = [_f("a"), _f("b")]
    assert dedup_findings(candidates, ["a", "b"]) == []
