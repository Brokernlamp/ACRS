#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${YELLOW}▶ Setting up desktop app...${NC}"

# 1. Backend setup
echo -e "${YELLOW}▶ Setting up backend...${NC}"
cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python init_db.py > /dev/null 2>&1
echo -e "${GREEN}✅ Backend ready${NC}"

# 2. Frontend setup
echo -e "${YELLOW}▶ Setting up frontend...${NC}"
cd "$ROOT/frontend"
npm install --silent
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo -e "${GREEN}✅ Frontend ready${NC}"

# 3. Desktop setup
echo -e "${YELLOW}▶ Setting up Electron...${NC}"
cd "$ROOT/desktop"
npm install --silent
echo -e "${GREEN}✅ Electron ready${NC}"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "  Run the desktop app:  ./desktop-dev.sh"
echo "  Build Windows .exe:   ./desktop-build.sh"
echo ""
