import pytest
import scripts.io_utils as io_utils
from scripts.io_utils import atomic_write_text


def test_atomic_write_text_writes(tmp_path):
    p = tmp_path / "a.txt"
    atomic_write_text(p, "hello")
    assert p.read_text() == "hello"


def test_atomic_write_text_overwrites(tmp_path):
    p = tmp_path / "a.txt"
    atomic_write_text(p, "one")
    atomic_write_text(p, "two")
    assert p.read_text() == "two"
    assert [x.name for x in tmp_path.iterdir()] == ["a.txt"]  # no temp left


def test_atomic_write_text_failure_preserves_original(tmp_path, monkeypatch):
    p = tmp_path / "a.txt"
    atomic_write_text(p, "original")

    def boom(*a, **k):
        raise RuntimeError("disk full")

    monkeypatch.setattr(io_utils.os, "fsync", boom)
    with pytest.raises(RuntimeError):
        atomic_write_text(p, "new")
    assert p.read_text() == "original"
    assert [x.name for x in tmp_path.iterdir()] == ["a.txt"]  # no temp left
