import hashlib
from scripts.observers import data_observer


def test_data_observer_hash_matches_full_read(tmp_path):
    f = tmp_path / "results.csv"
    content = b"col1,col2\n" + b"x,y\n" * 5000  # a few KB, multiple chunks if chunk size were tiny
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()[:16]
    spec = {"id": "data", "observe": {"inputs": [str(f)]}}
    out = data_observer(spec)
    assert len(out) == 1
    assert out[0]["dedup_key"] == f"results.csv:{expected}"  # streaming digest == full-read digest


def test_data_observer_detects_change(tmp_path):
    f = tmp_path / "results.csv"
    f.write_bytes(b"v1")
    spec = {"id": "data", "observe": {"inputs": [str(f)]}}
    k1 = data_observer(spec)[0]["dedup_key"]
    f.write_bytes(b"v2")
    k2 = data_observer(spec)[0]["dedup_key"]
    assert k1 != k2
