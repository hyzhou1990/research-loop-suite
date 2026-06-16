# Loop Engine Protocol

`run_iteration(spec, state, observer)` is pure (no I/O). One iteration:

1. `candidates = observer(spec)` — read-only; each candidate carries a `dedup_key`.
2. `new = dedup_findings(candidates, state.seen_keys)`.
3. Advance state: `iteration += 1`; extend `seen_keys`; `empty_streak = 0 if new else +1`.
4. `decision = evaluate_stop(spec, state, new)`:
   - `iteration >= stop.max_iterations` → **exit**
   - `empty_streak >= stop.exit_when.empty_iterations` → **exit**
   - any new finding `severity >= stop.pause_for_human_when.severity_at_least` → **pause**
   - else → **continue**
5. `status = {pause: blocked, exit: exited, continue: active}`.

The CLI shell (`loop_run.run_once`) wraps this with I/O: load/save state, append inbox, write a
`BLOCKED-<watcher>` marker on pause.

Idempotency guarantee: re-running with identical observer output yields zero new findings and an
unchanged inbox (only `iteration`/`empty_streak` advance).
