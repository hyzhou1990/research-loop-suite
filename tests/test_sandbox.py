import os
import pytest
from pathlib import Path
from scripts.sandbox import observe_sandbox, SandboxViolation


def _dirs(tmp_path):
    project = tmp_path / "proj"
    runtime = project / ".research-loop"
    (runtime / "inbox").mkdir(parents=True)
    return project, runtime


def test_blocks_write_under_project(tmp_path):
    project, runtime = _dirs(tmp_path)
    target = project / "manuscript.md"
    with pytest.raises(SandboxViolation):
        with observe_sandbox(project, runtime):
            with open(target, "w") as fh:
                fh.write("malicious edit")
    assert not target.exists()  # write never happened


def test_allows_write_inside_runtime(tmp_path):
    project, runtime = _dirs(tmp_path)
    target = runtime / "inbox" / "scratch.txt"
    with observe_sandbox(project, runtime):
        with open(target, "w") as fh:
            fh.write("ok")
    assert target.read_text() == "ok"


def test_allows_write_outside_project(tmp_path):
    project, runtime = _dirs(tmp_path)
    outside = tmp_path / "elsewhere.txt"  # not under project
    with observe_sandbox(project, runtime):
        with open(outside, "w") as fh:
            fh.write("fine")
    assert outside.read_text() == "fine"


def test_allows_reads_under_project(tmp_path):
    project, runtime = _dirs(tmp_path)
    data = project / "results.csv"
    data.write_text("a,b\n1,2\n")  # created BEFORE sandbox
    with observe_sandbox(project, runtime):
        content = data.read_text()  # read is allowed
    assert "a,b" in content


def test_blocks_os_replace_under_project(tmp_path):
    project, runtime = _dirs(tmp_path)
    src = tmp_path / "src.txt"; src.write_text("x")
    dst = project / "data.csv"
    with pytest.raises(SandboxViolation):
        with observe_sandbox(project, runtime):
            os.replace(src, dst)
    assert not dst.exists()


def test_inactive_after_context_exits(tmp_path):
    project, runtime = _dirs(tmp_path)
    target = project / "after.md"
    with observe_sandbox(project, runtime):
        pass
    # outside the context, writes to the project are unrestricted again
    with open(target, "w") as fh:
        fh.write("ok")
    assert target.exists()
