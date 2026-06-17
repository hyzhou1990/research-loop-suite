import sys
from pathlib import Path

from scripts.state import load_state, save_state
from scripts.loop_engine import run_iteration
from scripts.inbox import append_findings
from scripts.observers import get_observer
from scripts.specs import load_spec
from scripts.locking import watcher_lock, LoopBusy
from scripts.sandbox import observe_sandbox
from scripts.findings import make_finding


def run_once(spec_path, project_root, observer=None):
    spec = load_spec(spec_path)
    watcher_id = spec["id"]
    project_root = Path(project_root)
    runtime = project_root / ".research-loop"
    state_path = runtime / "state" / f"{watcher_id}.json"

    try:
        with watcher_lock(runtime, watcher_id):
            state = load_state(state_path, watcher_id)
            obs = observer or get_observer(watcher_id)

            def guarded(s, _obs=obs, _proj=project_root, _rt=runtime):
                with observe_sandbox(_proj, _rt):
                    return _obs(s)

            try:
                res = run_iteration(spec, state, guarded)
            except Exception as e:
                # Observer failure (sandbox violation, network/API error, bug) is
                # isolated: record it, leave state untouched, do not crash the run.
                err = make_finding(
                    dedup_key=f"observer-error:{watcher_id}:{type(e).__name__}",
                    type="observer_error",
                    severity="high",
                    item=f"{watcher_id} observer failed: {type(e).__name__}",
                    why_it_matters=(str(e)[:500] or type(e).__name__),
                    suggested_action="inspect the observer/source; the watcher made no progress this run",
                )
                append_findings(runtime / "inbox", watcher_id, [err])
                return {
                    "new_findings": [err],
                    "state": None,
                    "decision": "error",
                    "error": f"{type(e).__name__}: {e}",
                }

            append_findings(runtime / "inbox", watcher_id, res["new_findings"])
            save_state(state_path, res["state"])

            if res["decision"] == "pause":
                runtime.mkdir(parents=True, exist_ok=True)
                (runtime / f"BLOCKED-{watcher_id}").write_text(
                    f"Paused for human review at iteration {res['state']['iteration']}.\n"
                )
            return res
    except LoopBusy:
        return {"new_findings": [], "state": None, "decision": "skipped"}


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) < 2:
        print("usage: loop_run.py <spec.yaml> <project_root>", file=sys.stderr)
        return 2
    res = run_once(argv[0], argv[1])
    print(f"{res['decision']}: {len(res['new_findings'])} new finding(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
