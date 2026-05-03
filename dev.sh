#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

# ── Kill anything already on our ports ────────────────────────────────────────
echo -e "${YELLOW}▶ Clearing ports 8000 and 3000...${NC}"

for PORT in 8000 3000; do
  PIDS=$(lsof -ti:$PORT 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "  Killing process(es) on port $PORT: $PIDS"
    echo "$PIDS" | xargs kill -9 2>/dev/null || true
    sleep 0.5
  else
    echo "  Port $PORT is free"
  fi
done

# ── Check setup ───────────────────────────────────────────────────────────────
if [ ! -d "$ROOT/backend/.venv" ]; then
  echo -e "${RED}❌ Virtual environment not found. Run ./setup.sh first.${NC}"
  exit 1
fi

if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo -e "${RED}❌ Node modules not found. Run ./setup.sh first.${NC}"
  exit 1
fi

# ── Start backend ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}▶ Starting backend  →  http://localhost:8000${NC}"
cd "$ROOT/backend"
.venv/bin/uvicorn main:app --reload --port 8000 --log-level warning &
BACKEND_PID=$!

# ── Start frontend ────────────────────────────────────────────────────────────
echo -e "${YELLOW}▶ Starting frontend →  http://localhost:3000${NC}"
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✅ Both servers running.${NC}"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "   Press Ctrl+C to stop both."
echo ""

# ── Cleanup on exit ───────────────────────────────────────────────────────────
trap "
  echo ''
  echo -e '${YELLOW}▶ Stopping servers...${NC}'
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  # Kill anything still on the ports
  lsof -ti:8000 | xargs kill -9 2>/dev/null || true
  lsof -ti:3000 | xargs kill -9 2>/dev/null || true
  echo -e '${GREEN}✅ Stopped.${NC}'
  exit 0
" INT TERM

wait
