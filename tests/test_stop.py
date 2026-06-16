from scripts.loop_engine import evaluate_stop
from scripts.findings import make_finding


def _spec(**stop):
    return {"id": "lit", "stop": stop}


def test_exit_on_max_iterations():
    spec = _spec(max_iterations=5)
    state = {"iteration": 5, "empty_streak": 0}
    assert evaluate_stop(spec, state, []) == "exit"


def test_pause_on_high_severity_new_finding():
    spec = _spec(max_iterations=100, pause_for_human_when={"severity_at_least": "high"})
    state = {"iteration": 2, "empty_streak": 0}
    new = [make_finding("k", "t", "critical", "i", "w", "a")]
    assert evaluate_stop(spec, state, new) == "pause"


def test_exit_on_empty_streak():
    spec = _spec(max_iterations=100, exit_when={"empty_iterations": 3})
    state = {"iteration": 9, "empty_streak": 3}
    assert evaluate_stop(spec, state, []) == "exit"


def test_continue_otherwise():
    spec = _spec(max_iterations=100, pause_for_human_when={"severity_at_least": "critical"})
    state = {"iteration": 1, "empty_streak": 0}
    new = [make_finding("k", "t", "low", "i", "w", "a")]
    assert evaluate_stop(spec, state, new) == "continue"
