#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

export PATH="$HOME/.local/bin:$PATH"

if [ -f "$ROOT_DIR/deploy/laptop/main-backend.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/deploy/laptop/main-backend.env"
  set +a
fi

export CONTENT_ANALYSIS_WORKER_URL="${CONTENT_ANALYSIS_WORKER_URL:-http://127.0.0.1:8001}"
export CONTENT_ANALYSIS_WORKER_TOKEN="${CONTENT_ANALYSIS_WORKER_TOKEN:-}"

cd "$BACKEND_DIR"
exec uv run uvicorn main:app --host 0.0.0.0 --port 8000
