#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

# ── Kill anything on our ports ────────────────────────────────────────────────
echo -e "${YELLOW}▶ Clearing ports 8000 and 3000...${NC}"
for PORT in 8000 3000; do
  PIDS=$(lsof -ti:$PORT 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "  Killing process(es) on port $PORT: $PIDS"
    echo "$PIDS" | xargs kill -9 2>/dev/null || true
    sleep 0.5
  fi
done

# ── Check setup ───────────────────────────────────────────────────────────────
if [ ! -d "$ROOT/backend/.venv" ]; then
  echo -e "${RED}❌ Run ./desktop-setup.sh first${NC}"
  exit 1
fi

if [ ! -d "$ROOT/desktop/node_modules" ]; then
  echo -e "${RED}❌ Run ./desktop-setup.sh first${NC}"
  exit 1
fi

echo -e "${YELLOW}▶ Launching AI Growth Operator (desktop mode)...${NC}"
cd "$ROOT/desktop"
npm run dev
