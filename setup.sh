#!/bin/bash
set -e

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
step() { echo -e "\n${YELLOW}▶ $1${NC}"; }

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       AI Growth Operator — Setup         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Check prerequisites ────────────────────────────────────────────────────
step "Checking prerequisites"

command -v python3 >/dev/null 2>&1 || err "Python 3.10+ is required. Install from https://python.org"
PY_VER=$(python3 -c "import sys; print(sys.version_info.minor)")
[ "$PY_VER" -ge 10 ] || err "Python 3.10+ required (found 3.$PY_VER)"
ok "Python 3.$PY_VER"

command -v node >/dev/null 2>&1 || err "Node.js 18+ is required. Install from https://nodejs.org"
NODE_VER=$(node -e "console.log(process.versions.node.split('.')[0])")
[ "$NODE_VER" -ge 18 ] || err "Node.js 18+ required (found $NODE_VER)"
ok "Node.js $NODE_VER"

command -v npm >/dev/null 2>&1 || err "npm is required"
ok "npm $(npm --version)"

# ── 2. Backend env file ───────────────────────────────────────────────────────
step "Configuring backend environment"

ENV_FILE="$ROOT/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
  cp "$ROOT/backend/.env.example" "$ENV_FILE" 2>/dev/null || cat > "$ENV_FILE" << 'EOF'
APP_ENV=development
DEBUG=False
SECRET_KEY=change-me-in-production
DATABASE_URL=sqlite:///./acrs.db
JWT_SECRET_KEY=change-me-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
GEMINI_API_KEY=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=
SMTP_PASSWORD=
EOF
  warn ".env created — add your GEMINI_API_KEY to backend/.env to enable the AI chatbot"
else
  ok ".env already exists"
fi

# ── 3. Backend Python venv ────────────────────────────────────────────────────
step "Setting up Python virtual environment"

cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  ok "Virtual environment created"
else
  ok "Virtual environment already exists"
fi

step "Installing Python dependencies (this may take a minute)"
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
ok "Python dependencies installed"

# ── 4. Database ───────────────────────────────────────────────────────────────
step "Initialising database"
.venv/bin/python init_db.py > /dev/null 2>&1
ok "Database ready"

# Seed default user if not present
.venv/bin/python - << 'PYEOF'
from database import SessionLocal
from database.models import User
from database.crud import create_user
from auth import hash_password
db = SessionLocal()
if not db.query(User).filter(User.id == 1).first():
    create_user(db, email="admin@acrs.com", password_hash=hash_password("admin123"), full_name="Admin")
    print("Default user created: admin@acrs.com / admin123")
db.close()
PYEOF
ok "Default user ready (admin@acrs.com)"

# ── 5. Frontend ───────────────────────────────────────────────────────────────
step "Installing frontend dependencies"
cd "$ROOT/frontend"

if [ ! -f ".env.local" ]; then
  echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
  ok ".env.local created"
fi

npm install --silent
ok "Frontend dependencies installed"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Setup complete! 🎉             ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  To start the app, run:"
echo ""
echo "    ./dev.sh"
echo ""
echo "  Then open: http://localhost:3000"
echo ""
echo "  Optional — add your Gemini API key for AI chat:"
echo "    Edit backend/.env  →  GEMINI_API_KEY=your-key-here"
echo ""
echo "  Sample data to test with: backend/sample_data.csv"
echo ""
