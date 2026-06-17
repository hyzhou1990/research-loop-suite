from urllib.parse import urlparse, parse_qs
from scripts.openalex import build_url


def _params(url):
    return parse_qs(urlparse(url).query)


def test_build_url_basic_query():
    url = build_url("RSV prefusion F")
    assert url.startswith("https://api.openalex.org/works?")
    p = _params(url)
    assert p["search"] == ["RSV prefusion F"]
    assert p["sort"] == ["publication_date:desc"]
    assert p["per-page"] == ["50"]
    assert "filter" not in p          # no from_date -> no filter
    assert "mailto" not in p          # no mailto -> omitted


def test_build_url_with_from_date_and_mailto():
    url = build_url("cancer", from_date="2026-01-01", mailto="a@b.com", per_page=10)
    p = _params(url)
    assert p["filter"] == ["from_publication_date:2026-01-01"]
    assert p["mailto"] == ["a@b.com"]
    assert p["per-page"] == ["10"]


def test_build_url_encodes_special_chars():
    url = build_url("p53 & MDM2")
    p = _params(url)
    assert p["search"] == ["p53 & MDM2"]   # round-trips through encoding


from scripts.openalex import parse_works


def _payload(results, count=None):
    return {"results": results, "meta": {"count": count if count is not None else len(results)}}


def test_parse_works_maps_fields():
    payload = _payload([{
        "id": "https://openalex.org/W1",
        "doi": "https://doi.org/10.1/x",
        "title": "Prefusion F antigen design",
        "publication_year": 2026,
        "publication_date": "2026-05-01",
        "cited_by_count": 7,
    }])
    out = parse_works(payload, "RSV")
    assert len(out) == 1
    f = out[0]
    assert f["dedup_key"] == "https://openalex.org/W1"
    assert f["type"] == "new_paper"
    assert f["severity"] == "medium"
    assert "Prefusion F antigen design" in f["item"]
    assert "2026" in f["item"]
    assert "RSV" in f["why_it_matters"]
    assert "cited-by 7" in f["why_it_matters"]
    assert "10.1/x" in f["suggested_action"]


def test_parse_works_empty():
    assert parse_works(_payload([]), "x") == []


def test_parse_works_handles_missing_fields():
    # no title, no doi, no cited_by_count, but has id -> still produces a finding
    payload = _payload([{"id": "https://openalex.org/W2"}])
    out = parse_works(payload, "x")
    assert len(out) == 1
    assert out[0]["dedup_key"] == "https://openalex.org/W2"
    assert "(untitled)" in out[0]["item"]
    # falls back to the OpenAlex url in the action since no doi
    assert "openalex.org/W2" in out[0]["suggested_action"]


def test_parse_works_falls_back_to_doi_when_no_id():
    payload = _payload([{"doi": "https://doi.org/10.2/y", "title": "T"}])
    out = parse_works(payload, "x")
    assert out[0]["dedup_key"] == "https://doi.org/10.2/y"


def test_parse_works_skips_work_without_id_or_doi():
    payload = _payload([{"title": "no identifiers"}])
    assert parse_works(payload, "x") == []


def test_parse_works_appends_coverage_note_when_truncated():
    # meta.count (100) > returned results (1) -> advisory coverage note
    payload = _payload([{"id": "https://openalex.org/W1", "title": "T"}], count=100)
    out = parse_works(payload, "topic")
    assert len(out) == 2
    note = out[-1]
    assert note["type"] == "coverage_note"
    assert note["severity"] == "low"
    assert "100" in note["why_it_matters"]
    # stable dedup key per (query, count) so it is not re-reported every run
    assert note["dedup_key"] == "coverage:topic:100"


import json
import io
import pytest
import scripts.openalex as oa


class _FakeResp(io.BytesIO):
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def test_fetch_works_parses_json(monkeypatch):
    payload = {"results": [{"id": "W1"}], "meta": {"count": 1}}

    def fake_urlopen(req, timeout=None):
        return _FakeResp(json.dumps(payload).encode())

    monkeypatch.setattr(oa.urllib.request, "urlopen", fake_urlopen)
    out = oa.fetch_works("https://api.openalex.org/works?search=x")
    assert out == payload


def test_fetch_works_raises_on_persistent_error(monkeypatch):
    calls = {"n": 0}

    def always_fail(req, timeout=None):
        calls["n"] += 1
        raise OSError("connection refused")

    monkeypatch.setattr(oa.urllib.request, "urlopen", always_fail)
    monkeypatch.setattr(oa.time, "sleep", lambda *_: None)  # no real backoff delay
    with pytest.raises(RuntimeError):
        oa.fetch_works("https://api.openalex.org/works?search=x")
    assert calls["n"] == 2  # one retry then give up


def test_parse_works_skips_non_dict_work():
    payload = _payload([None, "junk", {"id": "https://openalex.org/W1", "title": "T"}])
    out = parse_works(payload, "x")
    assert len(out) == 1
    assert out[0]["dedup_key"] == "https://openalex.org/W1"


def test_parse_works_handles_null_cited_by_count():
    payload = _payload([{"id": "https://openalex.org/W1", "title": "T", "cited_by_count": None}])
    out = parse_works(payload, "x")
    assert "cited-by 0" in out[0]["why_it_matters"]


def test_fetch_works_does_not_mask_programming_errors(monkeypatch):
    def boom(req, timeout=None):
        raise TypeError("a real bug, not a transient failure")
    monkeypatch.setattr(oa.urllib.request, "urlopen", boom)
    monkeypatch.setattr(oa.time, "sleep", lambda *_: None)
    with pytest.raises(TypeError):
        oa.fetch_works("https://api.openalex.org/works?search=x")
