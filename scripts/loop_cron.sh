#!/usr/bin/env bash
# Cron/scheduled-agent adapter: one iteration of a watcher, gate enforced.
# Usage: loop_cron.sh <watcher_id> <project_root>
set -euo pipefail
SUITE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WATCHER="$1"
PROJECT="$2"
export RESEARCH_LOOP_ACTIVE=1
export RESEARCH_LOOP_RUNTIME="${PROJECT}/.research-loop"
cd "$SUITE_ROOT"
python3 -m scripts.loop_run "watchers/${WATCHER}.yaml" "$PROJECT"
