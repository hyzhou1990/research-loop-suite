import subprocess
import sys
from pathlib import Path
from scripts.inbox import append_findings
from scripts.findings import make_finding


def test_inbox_cli_prints_digest(tmp_path):
    inbox = tmp_path / "inbox"
    append_findings(inbox, "lit", [make_finding("a", "new_paper", "high", "Smith 2026", "matches RQ", "read")])
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.inbox", str(inbox)],
        capture_output=True, text=True, cwd=str(Path.cwd()),
    )
    assert proc.returncode == 0
    assert "Smith 2026" in proc.stdout
    assert "HIGH" in proc.stdout


def test_inbox_cli_usage_without_args():
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.inbox"],
        capture_output=True, text=True, cwd=str(Path.cwd()),
    )
    assert proc.returncode == 2
