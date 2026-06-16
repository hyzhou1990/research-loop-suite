import pytest
from scripts.observers import register, get_observer, REGISTRY


def test_register_and_get():
    @register("dummy")
    def dummy(spec):
        return []
    assert get_observer("dummy") is dummy


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        get_observer("does-not-exist-xyz")


def test_builtin_observers_registered():
    for wid in ["lit", "manuscript", "data", "field"]:
        assert wid in REGISTRY
