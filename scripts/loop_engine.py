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
        t = SEVERITY_ORDER[threshold]
        if any(SEVERITY_ORDER[f["severity"]] >= t for f in new_findings):
            return "pause"

    return "continue"
