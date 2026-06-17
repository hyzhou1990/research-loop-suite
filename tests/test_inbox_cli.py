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


def test_cli_ack_marks_and_prints(tmp_path):
    inbox = tmp_path / "inbox"
    append_findings(inbox, "lit", [make_finding("https://openalex.org/W1", "new_paper", "medium", "P1", "w", "a")])
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.inbox", str(inbox), "ack", "https://openalex.org/W1"],
        capture_output=True, text=True, cwd=str(Path.cwd()),
    )
    assert proc.returncode == 0
    assert "ack" in proc.stdout
    # persisted
    from scripts.inbox import _read_all
    assert _read_all(inbox)[0]["status"] == "ack"


def test_cli_dismiss_then_digest_hides_then_all_shows(tmp_path):
    inbox = tmp_path / "inbox"
    append_findings(inbox, "lit", [make_finding("k-x", "new_paper", "medium", "Hidden Paper", "w", "a")])
    subprocess.run([sys.executable, "-m", "scripts.inbox", str(inbox), "dismiss", "k-x"],
                   capture_output=True, text=True, cwd=str(Path.cwd()))
    digest = subprocess.run([sys.executable, "-m", "scripts.inbox", str(inbox)],
                            capture_output=True, text=True, cwd=str(Path.cwd()))
    assert "Hidden Paper" not in digest.stdout
    all_digest = subprocess.run([sys.executable, "-m", "scripts.inbox", str(inbox), "--all"],
                                capture_output=True, text=True, cwd=str(Path.cwd()))
    assert "Hidden Paper" in all_digest.stdout


def test_cli_bad_prefix_exits_2(tmp_path):
    inbox = tmp_path / "inbox"
    append_findings(inbox, "lit", [make_finding("k-y", "new_paper", "medium", "P", "w", "a")])
    proc = subprocess.run([sys.executable, "-m", "scripts.inbox", str(inbox), "ack", "nope"],
                          capture_output=True, text=True, cwd=str(Path.cwd()))
    assert proc.returncode == 2
