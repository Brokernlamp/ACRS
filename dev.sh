#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Check setup has been run
if [ ! -d "$ROOT/backend/.venv" ]; then
  echo "❌ Run ./setup.sh first"
  exit 1
fi

echo "▶ Starting backend  →  http://localhost:8000"
cd "$ROOT/backend"
.venv/bin/uvicorn main:app --reload --port 8000 --log-level warning &
BACKEND_PID=$!

echo "▶ Starting frontend →  http://localhost:3000"
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers running. Press Ctrl+C to stop."
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'; exit" INT TERM
wait
