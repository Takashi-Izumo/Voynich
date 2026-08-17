#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python}"
export PYTHONPATH="$ROOT/code${PYTHONPATH:+:$PYTHONPATH}"
"$PYTHON" code/12_run_all.py --root "$ROOT" --budget-runs "${BUDGET_RUNS:-50}" "$@"
