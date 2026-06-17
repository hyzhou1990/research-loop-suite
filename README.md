# research-loop-suite

A **loop-native research suite**: a lean engine that runs declarative *watcher* specs which keep observing a research project unattended — the literature, your manuscript, your data, the field — and flag findings to a human inbox.

> **The one invariant:** _Observe autonomously. Mutate only behind a human gate._
> A loop may search, read, diff, score, and flag. It never edits your manuscript or data, and it can only write inside `.research-loop/`. Acting on a finding is always a human decision.

[![tests](https://img.shields.io/badge/tests-52%20passing-brightgreen)](#development)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

---

## Why

Most research tooling runs once, under supervision: research → write → review, then stop. This suite inverts that. Instead of a linear pipeline, it is a set of small standing loops ("watchers") that keep watching the work and surface what changed — a new contradicting paper, a citation that no longer holds, a data artifact whose hash drifted, a competing preprint. You stay the pilot; the loops do the watching.

It is deliberately **brief at the core**: one code-bearing engine, and every watcher is a single YAML file. Adding a new watcher costs one config file plus one observer function — no new skill, no engine changes.

## How it works

```
watcher.yaml ──▶ loop engine (one iteration) ──▶ .research-loop/inbox/
   cadence          load state                       findings (JSONL)
   observe          observe() — read only                 │
   flag             dedup vs seen_keys                     ▼
   stop             score → append inbox             digest (Markdown)
                    update state
                    decide: continue / pause / exit
```

Each iteration is **idempotent**: re-running with no new input yields zero new findings.

### The watch-spec contract

Every watcher is the same four blocks:

```yaml
id: lit
cadence: { mode: self-paced, every: 1d }
observe:
  target: "saved bibliography + research question"
  how: "query Semantic Scholar / OpenAlex / Crossref for new/retracted/contradictory papers"
  inputs: []
flag:
  fields: [type, severity, item, why_it_matters, suggested_action]
  dedup_key: "paper DOI or id"
stop:
  pause_for_human_when: { severity_at_least: critical }
  exit_when: { empty_iterations: 5 }
  max_iterations: 100
```

### Built-in watchers

| id | watches | observe | status |
|----|---------|---------|--------|
| `data` | result/data artifacts | content-hash drift (reproducibility) | **functional** |
| `lit` | literature landscape | new / retracted / contradictory papers | stub (returns `[]`) |
| `field` | preprints / competing labs | scoop-risk, emerging methods | stub (returns `[]`) |
| `manuscript` | the active draft | claim-integrity, citation-faithfulness | stub (returns `[]`) |

> The `data` watcher is fully wired and proven end-to-end. The other three are intentional stubs: the engine, gate, inbox, dedup, and scheduling are complete, and each remaining watcher needs only its observer wired to a real source.

## Quick start

Run from the suite root:

```bash
# one iteration of a watcher against a target project
python3 -m scripts.loop_run watchers/data.yaml /path/to/your/project

# view the inbox digest
python3 -m scripts.inbox /path/to/your/project/.research-loop/inbox
```

State lives in `<project>/.research-loop/state/<watcher>.json`; findings in `<project>/.research-loop/inbox/<watcher>.jsonl`.

## Schedulers

All three call the same entrypoint — a watcher doesn't care which fires it:

- **Manual** — `python3 -m scripts.loop_run …` (above)
- **Cron / unattended** — `scripts/loop_cron.sh <watcher> <project>` (sets the gate env contract)
- **In-session** — under a `/loop`, re-invoking per tick at the spec's `cadence.every`

See [`research-loop/references/adapters.md`](research-loop/references/adapters.md).

## The gate (observe-only enforcement)

A `PreToolUse` hook (`scripts/write_scope_guard.py`, wired via `hooks/hooks.json`) enforces the invariant during a loop run:

- blocks `Write` / `Edit` / `MultiEdit` to any path outside the project's `.research-loop/`
- blocks `Bash` entirely during a loop (its writes can't be scoped)
- uses normalized **path containment** anchored to `RESEARCH_LOOP_RUNTIME` (not a substring match)
- **fails closed** on unparseable input while a loop is active

> ⚠️ **Important limitation.** The gate is a Claude-harness hook. The **unattended `cron` path runs a bare Python process with no hook**, so today its observe-only guarantee rests on the observers being pure read-only Python. Before shipping any observer that gains network/LLM/file-write capability, either run cron under a hooked harness or add an in-process scope check.

## Layout

```
research-loop/        SKILL.md (≤150 lines) + references (protocol, watch-spec guide, adapters)
watchers/             the four watcher specs (data, lit, field, manuscript)
shared/               loop_state.schema.json, flag.schema.json
scripts/              loop_engine.py (pure core), loop_run.py (I/O shell), state.py,
                      findings.py, inbox.py, observers.py, write_scope_guard.py, loop_cron.sh
hooks/                hooks.json (wires the gate)
tests/                pytest suite
```

## Authoring a new watcher

1. Add `watchers/<id>.yaml` with the four blocks above.
2. Register an observer in `scripts/observers.py` under the same `id`; it takes the spec and returns a list of findings (built with `findings.make_finding(...)`), each carrying a unique `dedup_key`.

The engine handles dedup, scoring, the inbox, state, and stop logic — the observer only has to *find things*. See [`research-loop/references/watch_spec_guide.md`](research-loop/references/watch_spec_guide.md).

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q          # 52 passing
```

### Smoke test

Run the whole pipeline end-to-end (data-watcher lifecycle + write-scope gate) in one command before deploys or in CI; it exits non-zero if anything is wrong.

```bash
scripts/smoke.sh
```

## License

[Apache-2.0](LICENSE) © 2026 hyzhou1990
