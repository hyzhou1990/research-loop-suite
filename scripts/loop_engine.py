import inspect


def call_observer(fn, spec, state):
    """Call an observer back-compatibly: 2+ required positional params -> fn(spec, state),
    else fn(spec). Falls back to fn(spec) if the signature cannot be introspected.

    Dispatch assumes plain positional signatures. An observer that wants `state` via a
    variadic (*args), keyword-only, or pre-bound-partial signature won't be detected as
    2-arg -- declare it explicitly as `def observer(spec, state)`.
    """
    try:
        required = [p for p in inspect.signature(fn).parameters.values()
                    if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                    and p.default is p.empty]
        n = len(required)
    except (TypeError, ValueError):
        n = 1
    return fn(spec, state) if n >= 2 else fn(spec)


def dedup_findings(candidates, seen_keys):
    seen = set(seen_keys)
    return [f for f in candidates if f["dedup_key"] not in seen]


SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def evaluate_stop(spec, state, new_findings):
    stop = spec.get("stop", {})
    max_iter = stop.get("max_iterations", 100)
    if state["iteration"] >= max_iter:
        return "exit"

    exit_when = stop.get("exit_when") or {}
    empty_target = exit_when.get("empty_iterations")
    if empty_target is not None and state["empty_streak"] >= empty_target:
        return "exit"

    pause = stop.get("pause_for_human_when") or {}
    threshold = pause.get("severity_at_least")
    if threshold is not None:
        if threshold not in SEVERITY_ORDER:
            raise ValueError(f"invalid severity_at_least in spec: {threshold!r}")
        t = SEVERITY_ORDER[threshold]
        if any(SEVERITY_ORDER[f["severity"]] >= t for f in new_findings):
            return "pause"

    return "continue"


_STATUS_BY_DECISION = {"pause": "blocked", "exit": "exited", "continue": "active"}


def run_iteration(spec, state, observer):
    raw = call_observer(observer, spec, state)
    if isinstance(raw, dict):
        candidates = raw.get("findings", [])
        new_cursor = raw.get("cursor", state.get("cursor"))
    else:
        candidates = raw
        new_cursor = state.get("cursor")

    new = dedup_findings(candidates, state["seen_keys"])

    new_state = dict(state)
    new_state["iteration"] = state["iteration"] + 1
    new_state["seen_keys"] = list(state["seen_keys"]) + [f["dedup_key"] for f in new]
    new_state["empty_streak"] = 0 if new else state.get("empty_streak", 0) + 1
    new_state["cursor"] = new_cursor

    decision = evaluate_stop(spec, new_state, new)
    new_state["status"] = _STATUS_BY_DECISION[decision]
    return {"new_findings": new, "state": new_state, "decision": decision}
