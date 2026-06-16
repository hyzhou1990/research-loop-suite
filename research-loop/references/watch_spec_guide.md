# Authoring a Watcher

A watcher is one YAML file in `watchers/`. Four blocks:

```yaml
id: my_watcher
cadence: { mode: self-paced|cron|manual, every: 1d }
observe:
  target: "what this looks at (human description)"
  how: "which observer function / API does the looking"
  inputs: [paths or identifiers the observer needs]
flag:
  fields: [type, severity, item, why_it_matters, suggested_action]
  dedup_key: "what makes a finding unique (documents the observer's key)"
stop:
  pause_for_human_when: { severity_at_least: high }
  exit_when: { empty_iterations: 3 }
  max_iterations: 100
```

Then register an observer in `scripts/observers.py` under the same `id`. The observer takes the
spec and returns a list of findings built with `findings.make_finding(...)`, each carrying a
unique `dedup_key`. The engine handles dedup, scoring, inbox, state, and stop logic — the
observer only has to *find things*.
