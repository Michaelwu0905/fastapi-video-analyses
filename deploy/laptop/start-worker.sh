#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT/backend"

if [ -f "$SCRIPT_DIR/worker.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/worker.env"
  set +a
fi

exec uv run uvicorn worker_main:app --host 0.0.0.0 --port 8001
