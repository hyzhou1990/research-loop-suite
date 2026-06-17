import os
import pytest
from scripts.openalex import build_url, fetch_works, parse_works

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE") != "1",
    reason="live OpenAlex test; set RUN_LIVE=1 to run",
)


def test_openalex_live_returns_findings():
    url = build_url("CRISPR", from_date="2026-01-01", mailto="research-loop@example.com", per_page=5)
    payload = fetch_works(url)
    findings = parse_works(payload, "CRISPR")
    assert isinstance(findings, list)
    # at least the request succeeded and produced a well-formed list
    for f in findings:
        assert f["dedup_key"]
        assert f["type"] in ("new_paper", "coverage_note")
