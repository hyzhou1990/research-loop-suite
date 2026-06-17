from scripts.loop_engine import call_observer


def test_call_observer_one_arg():
    seen = {}
    def obs(spec):
        seen["args"] = ("spec_only",)
        return ["x"]
    assert call_observer(obs, {"id": "a"}, {"cursor": None}) == ["x"]
    assert seen["args"] == ("spec_only",)


def test_call_observer_two_arg_receives_state():
    captured = {}
    def obs(spec, state):
        captured["state"] = state
        return {"findings": [], "cursor": "c"}
    out = call_observer(obs, {"id": "a"}, {"cursor": "prev"})
    assert captured["state"] == {"cursor": "prev"}
    assert out == {"findings": [], "cursor": "c"}


def test_call_observer_lambda_one_arg():
    assert call_observer(lambda spec: ["y"], {}, {}) == ["y"]


def test_call_observer_uninspectable_falls_back_to_one_arg():
    # builtins often can't be signature-introspected; must not raise, must call fn(spec)
    # len({...}) -> number of keys; proves it was called as fn(spec)
    assert call_observer(len, {"a": 1, "b": 2}, {"cursor": None}) == 2
