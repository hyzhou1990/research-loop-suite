from scripts.loop_run import run_once


def test_data_watcher_end_to_end(tmp_path):
    # Arrange: a project with one artifact and a data spec pointing at it
    project = tmp_path / "proj"
    project.mkdir()
    artifact = project / "results.csv"
    artifact.write_text("a,b\n1,2\n")

    spec = project / "data.yaml"
    spec.write_text(
        "id: data\n"
        "cadence: { mode: manual }\n"
        "observe:\n"
        "  target: artifacts\n"
        "  how: data observer\n"
        f"  inputs: ['{artifact}']\n"
        "flag: { dedup_key: 'artifact name + content hash' }\n"
        "stop: { max_iterations: 100, exit_when: { empty_iterations: 3 } }\n"
    )

    # Act 1: first run surfaces the artifact
    res1 = run_once(spec, project)
    assert len(res1["new_findings"]) == 1

    # Act 2: unchanged artifact → idempotent, zero new findings
    res2 = run_once(spec, project)
    assert res2["new_findings"] == []

    # Act 3: change the artifact → new finding (new hash)
    artifact.write_text("a,b\n9,9\n")
    res3 = run_once(spec, project)
    assert len(res3["new_findings"]) == 1
