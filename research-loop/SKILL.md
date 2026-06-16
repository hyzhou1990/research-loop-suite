---
name: research-loop
description: "Loop-native research engine. Runs declarative watcher specs that observe a research project unattended (literature, manuscript, data, field) and flag findings to a human inbox. Observe-only: never mutates the manuscript or data. Triggers on: watch literature, monitor my paper, watch my data, scoop risk, research loop, run watcher, set up a research watcher."
metadata:
  version: "0.1.0"
  status: active
  invariant: "observe autonomously, mutate only behind a human gate"
---

# Research Loop — Loop-Native Research Engine

A single engine that runs **watcher specs**: small declarative loops that observe a research
project and surface findings to a human inbox. The engine never edits your work.

## The invariant
**Observe autonomously. Mutate only behind a human gate.** A loop iteration may search, read,
diff, score, and flag — and may write *only* to `.research-loop/`. Editing the manuscript or
data is a human Tier-2 action, enforced by the `write_scope_guard` hook.

## Quick start
```
python3 -m scripts.loop_run watchers/lit.yaml /path/to/project   # one iteration
python3 -m scripts.inbox  /path/to/project/.research-loop/inbox  # digest (see references)
```

## What a watcher is
A YAML file with four parts: `cadence`, `observe`, `flag`, `stop`. Adding a watcher = one YAML
file, no code. See `references/watch_spec_guide.md`.

## Built-in watchers
| id | watches | observe |
|----|---------|---------|
| lit | literature landscape | new/retracted/contradictory papers vs bibliography |
| manuscript | the active draft | claim-integrity + citation-faithfulness |
| data | result artifacts | content-hash drift (reproducibility) |
| field | preprints/competing labs | scoop-risk + emerging methods |

## How it runs
Each iteration: load state → `observe` (read-only) → dedup vs `seen_keys` → score → append to
inbox → update state → evaluate `stop` (pause/exit/continue). See
`references/loop_engine_protocol.md`.

## Schedulers
Manual, cron (`scripts/loop_cron.sh`), or in-session `/loop`. All call the same entrypoint. See
`references/adapters.md`.

## Triage
Findings land in `.research-loop/inbox/<watcher>.jsonl`. Review the digest; graduate anything
worth acting on to a human Tier-2 edit. The loop will not do it for you.
