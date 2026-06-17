import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path


class SandboxViolation(Exception):
    """Raised when a sandboxed observer attempts to write inside the watched project."""


_state = threading.local()
_installed = False

_WRITE_OPEN_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC


def _active():
    return getattr(_state, "active", False)


def _check(path):
    project = _state.project
    runtime = _state.runtime
    try:
        resolved = Path(os.fsdecode(path)).resolve()
    except (ValueError, OSError):
        # If we cannot resolve it, fail closed.
        raise SandboxViolation(f"observe-only: cannot resolve write target {path!r}")
    under_project = resolved == project or project in resolved.parents
    under_runtime = resolved == runtime or runtime in resolved.parents
    if under_project and not under_runtime:
        raise SandboxViolation(
            f"observe-only sandbox: blocked write to {resolved} "
            f"(inside watched project, outside .research-loop/). "
            f"Observers must not mutate the project — graduate to a human Tier-2 action."
        )


def _audit(event, args):
    if not _active():
        return
    if event == "open":
        path, mode, flags = args
        if isinstance(path, int):
            return
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and bool(flags & _WRITE_OPEN_FLAGS)
        )
        if writing:
            _check(path)
    elif event in ("os.rename", "os.link", "os.symlink"):
        for p in args[:2]:
            _check(p)
    elif event in ("os.remove", "os.unlink", "os.mkdir", "os.rmdir", "os.truncate", "os.chmod"):
        _check(args[0])


def _ensure_installed():
    global _installed
    if not _installed:
        sys.addaudithook(_audit)
        _installed = True


@contextmanager
def observe_sandbox(project_root, runtime_dir):
    """While active, block writes inside project_root that are not under runtime_dir."""
    _ensure_installed()
    prev_active = getattr(_state, "active", False)
    prev_project = getattr(_state, "project", None)
    prev_runtime = getattr(_state, "runtime", None)
    _state.project = Path(project_root).resolve()
    _state.runtime = Path(runtime_dir).resolve()
    _state.active = True
    try:
        yield
    finally:
        _state.active = prev_active
        _state.project = prev_project
        _state.runtime = prev_runtime
