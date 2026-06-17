import fcntl
import os
from contextlib import contextmanager
from pathlib import Path


class LoopBusy(Exception):
    """Raised when another run holds this watcher's lock."""


@contextmanager
def watcher_lock(runtime_dir, watcher_id):
    lock_dir = Path(runtime_dir) / "state"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{watcher_id}.lock"
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            raise LoopBusy(f"watcher '{watcher_id}' is already running") from e
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
