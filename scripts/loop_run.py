import sys
import yaml
from pathlib import Path

from scripts.state import load_state, save_state
from scripts.loop_engine import run_iteration
from scripts.inbox import append_findings
from scripts.observers import get_observer


def run_once(spec_path, project_root, observer=None):
    spec = yaml.safe_load(Path(spec_path).read_text())
    watcher_id = spec["id"]
    project_root = Path(project_root)
    runtime = project_root / ".research-loop"
    state_path = runtime / "state" / f"{watcher_id}.json"

    state = load_state(state_path, watcher_id)
    obs = observer or get_observer(watcher_id)
    res = run_iteration(spec, state, obs)

    append_findings(runtime / "inbox", watcher_id, res["new_findings"])
    save_state(state_path, res["state"])

    if res["decision"] == "pause":
        runtime.mkdir(parents=True, exist_ok=True)
        (runtime / f"BLOCKED-{watcher_id}").write_text(
            f"Paused for human review at iteration {res['state']['iteration']}.\n"
        )
    return res


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
