#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$ROOT/backend/.venv" ]; then
  echo "❌ Run ./desktop-setup.sh first"
  exit 1
fi

if [ ! -d "$ROOT/desktop/node_modules" ]; then
  echo "❌ Run ./desktop-setup.sh first"
  exit 1
fi

echo "▶ Launching AI Growth Operator (desktop mode)..."
cd "$ROOT/desktop"
npm run dev
