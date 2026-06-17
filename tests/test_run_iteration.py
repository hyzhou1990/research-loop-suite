from scripts.loop_engine import run_iteration
from scripts.state import default_state
from scripts.findings import make_finding


def make_observer(keys):
    def observer(spec):
        return [make_finding(k, "new_paper", "low", k, "w", "a") for k in keys]
    return observer


def test_first_run_surfaces_all_and_advances_state():
    spec = {"id": "lit", "stop": {"max_iterations": 100, "exit_when": {"empty_iterations": 3}}}
    state = default_state("lit")
    res = run_iteration(spec, state, make_observer(["a", "b"]))
    assert [f["dedup_key"] for f in res["new_findings"]] == ["a", "b"]
    assert res["state"]["iteration"] == 1
    assert set(res["state"]["seen_keys"]) == {"a", "b"}
    assert res["state"]["empty_streak"] == 0
    assert res["decision"] == "continue"


def test_second_run_is_idempotent():
    spec = {"id": "lit", "stop": {"max_iterations": 100, "exit_when": {"empty_iterations": 3}}}
    state = default_state("lit")
    res1 = run_iteration(spec, state, make_observer(["a", "b"]))
    res2 = run_iteration(spec, res1["state"], make_observer(["a", "b"]))
    assert res2["new_findings"] == []
    assert res2["state"]["iteration"] == 2
    assert res2["state"]["empty_streak"] == 1


def test_pause_sets_blocked_status():
    spec = {"id": "lit", "stop": {"max_iterations": 100, "pause_for_human_when": {"severity_at_least": "high"}}}

    def observer(spec):
        return [make_finding("x", "retraction", "critical", "i", "w", "a")]

    res = run_iteration(spec, default_state("lit"), observer)
    assert res["decision"] == "pause"
    assert res["state"]["status"] == "blocked"


def test_exit_sets_exited_status():
    spec = {"id": "lit", "stop": {"max_iterations": 1}}
    res = run_iteration(spec, default_state("lit"), make_observer(["a"]))
    assert res["decision"] == "exit"
    assert res["state"]["status"] == "exited"


def test_run_iteration_persists_cursor_from_dict_observer():
    spec = {"id": "lit", "stop": {"max_iterations": 100, "exit_when": {"empty_iterations": 3}}}

    def dict_observer(spec, state):
        return {"findings": [], "cursor": "2026-06-15"}

    res = run_iteration(spec, default_state("lit"), dict_observer)
    assert res["state"]["cursor"] == "2026-06-15"


def test_run_iteration_list_observer_leaves_cursor():
    spec = {"id": "lit", "stop": {"max_iterations": 100, "exit_when": {"empty_iterations": 3}}}
    state = default_state("lit")
    state["cursor"] = "keep-me"
    res = run_iteration(spec, state, make_observer(["a"]))  # returns a list
    assert res["state"]["cursor"] == "keep-me"
    assert [f["dedup_key"] for f in res["new_findings"]] == ["a"]
