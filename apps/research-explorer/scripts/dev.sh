#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${APP_DIR}/../.." && pwd)"

BACKEND_HOST="${EXPLORER_API_HOST:-127.0.0.1}"
BACKEND_PORT="${EXPLORER_API_PORT:-8000}"
FRONTEND_HOST="${EXPLORER_FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${EXPLORER_FRONTEND_PORT:-5173}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "[research-explorer] Starting FastAPI backend on http://${BACKEND_HOST}:${BACKEND_PORT} ..."
(
  cd "${APP_DIR}"
  PYTHONPATH="${APP_DIR}:${REPO_ROOT}/src" uv run uvicorn backend.main:app \
    --host "${BACKEND_HOST}" \
    --port "${BACKEND_PORT}"
) &
BACKEND_PID=$!

echo "[research-explorer] Starting Vite frontend on http://${FRONTEND_HOST}:${FRONTEND_PORT} ..."
(
  cd "${APP_DIR}/frontend"
  npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}"
) &
FRONTEND_PID=$!

echo "[research-explorer] Workspace running locally:"
echo "  - Frontend UI: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "  - Backend API: http://${BACKEND_HOST}:${BACKEND_PORT}/api/health"
echo "Press Ctrl+C to stop both services."

wait
