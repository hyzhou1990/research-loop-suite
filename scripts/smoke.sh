#!/usr/bin/env bash
#
# End-to-end smoke test for research-loop-suite.
#
# Exercises the whole pipeline in one command and exits non-zero if anything
# is wrong, so it can be run before deploys and in CI.
#
# What it verifies:
#   data watcher lifecycle: first run flags 1 finding, re-run is idempotent
#   (0 findings), modifying the artifact re-flags 1 finding (drift detection).
#   inbox digest renders the artifact path and a MEDIUM severity group.
#   write-scope gate: blocks manuscript edits / Bash / cross-project writes,
#   allows writes inside this project's .research-loop/.
#
set -euo pipefail

# Resolve the suite root from this script's own location.
SUITE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Pick the interpreter robustly: prefer $PYTHON, then the venv, then python3.
PY="${PYTHON:-$SUITE_ROOT/.venv/bin/python}"
[ -x "$PY" ] || PY=python3

# Isolated demo project; always cleaned up.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PROJECT="$TMP/project"
RUNTIME="$PROJECT/.research-loop"
INBOX="$RUNTIME/inbox"
ARTIFACT="$PROJECT/results.csv"
SPEC="$TMP/data.yaml"

mkdir -p "$PROJECT"

# ---------------------------------------------------------------------------
# check() helper: records pass/fail without aborting under set -e.
# ---------------------------------------------------------------------------
FAILURES=0
check() {
  # usage: check "<description>" <0-or-1 condition-result>
  local desc="$1" ok="$2"
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s\n' "$desc"
  else
    printf 'FAIL: %s\n' "$desc"
    FAILURES=$((FAILURES + 1))
  fi
}

contains() {
  # contains "<haystack>" "<needle>" -> echoes 0 if found, 1 otherwise
  case "$1" in
    *"$2"*) echo 0 ;;
    *)      echo 1 ;;
  esac
}

run_loop() {
  # Run one data-watcher iteration; print combined stdout.
  ( cd "$SUITE_ROOT" && "$PY" -m scripts.loop_run "$SPEC" "$PROJECT" ) 2>&1
}

# Build a data watch-spec pointing at our artifact (the shipped spec has inputs: []).
cat > "$SPEC" <<EOF
id: data
cadence: { mode: manual }
observe:
  target: "result/data artifacts"
  how: "data observer: content-hash artifacts; flag changes"
  inputs:
    - "$ARTIFACT"
flag:
  fields: [type, severity, item, why_it_matters, suggested_action]
  dedup_key: "artifact name + content hash"
stop:
  pause_for_human_when: { severity_at_least: high }
  exit_when: { empty_iterations: 3 }
  max_iterations: 100
EOF

printf 'col\n1\n2\n3\n' > "$ARTIFACT"

# ---------------------------------------------------------------------------
# 1. First run on a fresh project -> 1 new finding.
# ---------------------------------------------------------------------------
OUT1="$(run_loop)"
check "first run flags 1 new finding (got: $(printf '%s' "$OUT1" | tr -d '\n'))" \
  "$(contains "$OUT1" "1 new finding")"

# ---------------------------------------------------------------------------
# 2. Second run, artifact unchanged -> 0 new findings (idempotent).
# ---------------------------------------------------------------------------
OUT2="$(run_loop)"
check "re-run is idempotent: 0 new findings (got: $(printf '%s' "$OUT2" | tr -d '\n'))" \
  "$(contains "$OUT2" "0 new finding")"

# ---------------------------------------------------------------------------
# 3. Modify the artifact, run again -> 1 new finding (drift detected).
# ---------------------------------------------------------------------------
printf 'col\n1\n2\n3\n4\n' > "$ARTIFACT"
OUT3="$(run_loop)"
check "drift detected after edit: 1 new finding (got: $(printf '%s' "$OUT3" | tr -d '\n'))" \
  "$(contains "$OUT3" "1 new finding")"

# ---------------------------------------------------------------------------
# 4. Inbox digest contains the artifact path AND the string MEDIUM.
# ---------------------------------------------------------------------------
DIGEST="$( ( cd "$SUITE_ROOT" && "$PY" -m scripts.inbox "$INBOX" ) 2>&1 )"
check "inbox digest contains the artifact path" \
  "$(contains "$DIGEST" "$ARTIFACT")"
check "inbox digest contains a MEDIUM severity group" \
  "$(contains "$DIGEST" "MEDIUM")"

# ---------------------------------------------------------------------------
# 4b. run-log + heartbeat + status (#9): the data runs above already created
#     $PROJECT/.research-loop, so the heartbeat and run-log must exist now.
# ---------------------------------------------------------------------------
check "heartbeat written" \
  "$([ -f "$PROJECT/.research-loop/last_run/data.json" ] && echo 0 || echo 1)"
check "run-log written" \
  "$([ -s "$PROJECT/.research-loop/log/data.jsonl" ] && echo 0 || echo 1)"

STATUS_OUT="$( ( cd "$SUITE_ROOT" && "$PY" -m scripts.status "$PROJECT" ) 2>/dev/null )"
check "status lists the data watcher" \
  "$(contains "$STATUS_OUT" "data")"

# ---------------------------------------------------------------------------
# 5. Write-scope gate (observe-only enforcement).
#    Capture non-zero exit codes safely so set -e does not abort.
# ---------------------------------------------------------------------------
export RESEARCH_LOOP_ACTIVE=1
export RESEARCH_LOOP_RUNTIME="$RUNTIME"
mkdir -p "$INBOX"

gate_rc() {
  # gate_rc "<json payload>" -> echoes the guard's exit code
  local payload="$1" rc
  set +e
  printf '%s' "$payload" | ( cd "$SUITE_ROOT" && "$PY" scripts/write_scope_guard.py ) >/dev/null 2>&1
  rc=$?
  set -e
  echo "$rc"
}

# 5a. Edit to a manuscript path OUTSIDE .research-loop/ -> blocked (exit 2).
RC="$(gate_rc "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$PROJECT/manuscript.md\"}}")"
check "gate blocks Edit to manuscript outside .research-loop (exit 2, got $RC)" \
  "$([ "$RC" -eq 2 ] && echo 0 || echo 1)"

# 5b. Write to a path INSIDE .research-loop/inbox/ -> allowed (exit 0).
RC="$(gate_rc "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$INBOX/note.txt\"}}")"
check "gate allows Write inside .research-loop/inbox (exit 0, got $RC)" \
  "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 5c. Bash tool -> blocked (exit 2).
RC="$(gate_rc "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"echo hi\"}}")"
check "gate blocks Bash during a loop (exit 2, got $RC)" \
  "$([ "$RC" -eq 2 ] && echo 0 || echo 1)"

# 5d. Write to a DIFFERENT project's .research-loop/ -> blocked (path anchoring).
RC="$(gate_rc "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"/tmp/other/.research-loop/x\"}}")"
check "gate blocks write to another project's .research-loop (exit 2, got $RC)" \
  "$([ "$RC" -eq 2 ] && echo 0 || echo 1)"

# ---------------------------------------------------------------------------
# Summary.
# ---------------------------------------------------------------------------
echo
if [ "$FAILURES" -eq 0 ]; then
  echo "smoke: ALL CHECKS PASSED"
  exit 0
else
  echo "smoke: $FAILURES CHECK(S) FAILED"
  exit 1
fi
