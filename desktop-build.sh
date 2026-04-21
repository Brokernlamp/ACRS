#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${YELLOW}▶ Building AI Growth Operator for Windows...${NC}"

# 1. Build Next.js frontend
echo -e "${YELLOW}▶ Building frontend...${NC}"
cd "$ROOT/frontend"
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
echo -e "${GREEN}✅ Frontend built${NC}"

# 2. Package with electron-builder
echo -e "${YELLOW}▶ Packaging with electron-builder...${NC}"
cd "$ROOT/desktop"
npm run build:win
echo -e "${GREEN}✅ Windows installer created in dist/${NC}"

echo ""
echo -e "${GREEN}✅ Build complete!${NC}"
echo "  Installer: dist/AI Growth Operator Setup*.exe"
echo ""
echo "  NOTE: To bundle Python on Windows, install PyInstaller and run:"
echo "    cd backend && pyinstaller --onedir main.py"
echo "  Then update extraResources in desktop/package.json to point to the dist folder."
echo ""
