#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    local status=$?
    trap - INT TERM EXIT

    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi

    wait "$BACKEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
    exit "$status"
}

trap cleanup INT TERM EXIT

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    printf 'Errore: python3 non è disponibile nel PATH e non esiste .venv/bin/python.\n' >&2
    exit 1
fi
command -v npm >/dev/null 2>&1 || {
    printf 'Errore: npm non è disponibile nel PATH.\n' >&2
    exit 1
}

if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
    printf 'Dipendenze frontend mancanti. Esegui prima: npm install --prefix frontend\n' >&2
    exit 1
fi

cd "$ROOT_DIR"
printf 'Backend:  http://localhost:8000\n'
printf 'Frontend: http://localhost:5173\n'
printf 'Interrompi entrambi con Ctrl+C.\n\n'

"$PYTHON_BIN" scripts/run_dashboard.py &
BACKEND_PID=$!
npm --prefix frontend run dev &
FRONTEND_PID=$!

wait -n "$BACKEND_PID" "$FRONTEND_PID"
