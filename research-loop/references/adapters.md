# Scheduler Adapters

All adapters call the same entrypoint: `scripts/loop_run.run_once(spec_path, project_root)`.

## Manual (one-shot)
```
python3 -m scripts.loop_run watchers/lit.yaml /path/to/project
```

## Cron / scheduled cloud agent (unattended)
```
*/0 8 * * *  /path/to/suite/scripts/loop_cron.sh lit /path/to/project
```
Sets `RESEARCH_LOOP_ACTIVE=1` so the write-scope gate is enforced. The adapter also exports `RESEARCH_LOOP_RUNTIME=<project>/.research-loop` so the write-scope guard enforces strong path-containment (not just the `.research-loop` name).

## In-session /loop (self-paced)
Run under the harness `/loop`, re-invoking `run_once` per tick and honoring the spec's
`cadence.every` for the wake interval. A `pause` decision (BLOCKED marker present) ends the loop
and asks the human to triage the inbox.
