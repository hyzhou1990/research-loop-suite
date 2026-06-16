import json
from pathlib import Path
import jsonschema
from scripts.findings import make_finding

SCHEMA = json.loads(Path("shared/flag.schema.json").read_text())


def test_make_finding_sets_status_new():
    f = make_finding("doi:10.1/x", "new_paper", "high", "Smith 2026", "matches RQ", "read + consider citing")
    assert f["status"] == "new"
    assert f["dedup_key"] == "doi:10.1/x"


def test_make_finding_conforms_to_schema():
    f = make_finding("doi:10.1/x", "new_paper", "high", "Smith 2026", "matches RQ", "read")
    jsonschema.validate(f, SCHEMA)


def test_make_finding_rejects_bad_severity():
    try:
        make_finding("k", "t", "urgent", "i", "w", "a")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_make_finding_rejects_empty_dedup_key():
    try:
        make_finding("", "t", "high", "i", "w", "a")
        assert False, "expected ValueError"
    except ValueError:
        pass
