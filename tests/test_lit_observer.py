import pytest
import yaml

import scripts.openalex as oa
from scripts.observers import get_observer
from scripts.loop_run import run_once

CANNED = {
    "results": [
        {"id": "https://openalex.org/W1", "doi": "https://doi.org/10.1/a",
         "title": "Paper A", "publication_year": 2026, "publication_date": "2026-05-01",
         "cited_by_count": 3},
    ],
    "meta": {"count": 1},
}


def test_lit_observer_returns_findings(monkeypatch):
    monkeypatch.setattr(oa, "fetch_works", lambda url, **k: CANNED)
    spec = {"id": "lit", "observe": {"inputs": {"query": "RSV", "from_date": "2026-01-01"}}}
    out = get_observer("lit")(spec)
    assert len(out) == 1
    assert out[0]["dedup_key"] == "https://openalex.org/W1"
    assert out[0]["type"] == "new_paper"


def test_lit_observer_requires_query():
    spec = {"id": "lit", "observe": {"inputs": {"from_date": "2026-01-01"}}}
    with pytest.raises(ValueError):
        get_observer("lit")(spec)


def test_lit_observer_rejects_non_mapping_inputs():
    spec = {"id": "lit", "observe": {"inputs": ["RSV"]}}  # list, not mapping
    with pytest.raises(ValueError):
        get_observer("lit")(spec)


def test_lit_observer_clamps_per_page(monkeypatch):
    captured = {}

    def fake_build_url(query, from_date=None, mailto=None, per_page=50):
        captured["per_page"] = per_page
        return "https://api.openalex.org/works?search=x"

    monkeypatch.setattr(oa, "build_url", fake_build_url)
    monkeypatch.setattr(oa, "fetch_works", lambda url, **k: {"results": [], "meta": {"count": 0}})
    spec = {"id": "lit", "observe": {"inputs": {"query": "RSV", "per_page": 9999}}}
    get_observer("lit")(spec)
    assert captured["per_page"] == 200  # clamped to OpenAlex max


def test_lit_observer_end_to_end_inbox(tmp_path, monkeypatch):
    monkeypatch.setattr(oa, "fetch_works", lambda url, **k: CANNED)
    spec = {
        "id": "lit", "cadence": {"mode": "manual"},
        "observe": {"target": "t", "how": "openalex", "inputs": {"query": "RSV"}},
        "flag": {"dedup_key": "id"},
        "stop": {"max_iterations": 100, "exit_when": {"empty_iterations": 3}},
    }
    spec_path = tmp_path / "lit.yaml"
    spec_path.write_text(yaml.safe_dump(spec))
    project = tmp_path / "proj"
    res = run_once(spec_path, project)   # uses the real registered lit observer
    assert res["decision"] == "continue"
    assert len(res["new_findings"]) == 1
    inbox = (project / ".research-loop" / "inbox" / "lit.jsonl").read_text()
    assert "openalex.org/W1" in inbox


def test_lit_observer_network_failure_isolated(tmp_path, monkeypatch):
    def boom(url, **k):
        raise RuntimeError("OpenAlex down")
    monkeypatch.setattr(oa, "fetch_works", boom)
    spec = {
        "id": "lit", "cadence": {"mode": "manual"},
        "observe": {"target": "t", "how": "openalex", "inputs": {"query": "RSV"}},
        "flag": {"dedup_key": "id"},
        "stop": {"max_iterations": 100, "exit_when": {"empty_iterations": 3}},
    }
    spec_path = tmp_path / "lit.yaml"
    spec_path.write_text(yaml.safe_dump(spec))
    project = tmp_path / "proj"
    res = run_once(spec_path, project)
    assert res["decision"] == "error"
    assert res["new_findings"][0]["type"] == "observer_error"
