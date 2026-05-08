# Windows Desktop Build — AI Growth Operator

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Node.js | 18+ | https://nodejs.org |
| Python | 3.10+ | https://python.org — check "Add to PATH" |
| Git | any | https://git-scm.com |

---

## 1 — One-time setup

```bat
cd ACRS

REM Backend Python venv
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
deactivate
cd ..

REM Frontend deps
cd frontend
npm install
cd ..

REM Desktop deps (includes keytar for OS credential storage)
cd desktop
npm install
cd ..
```

---

## 2 — Set environment variables

Create `backend\.env` (copy from `backend\.env.example`):

```
LICENSE_SERVER_URL=https://license.aigrowthoperator.com
DATABASE_URL=sqlite:///./acrs.db
SECRET_KEY=<random-64-chars>
JWT_SECRET_KEY=<random-64-chars>
ALLOWED_ORIGINS=http://localhost:3000
```

> The Gemini API key lives on the license server — do NOT add it here.

---

## 3 — Dev mode (no packaging)

```bat
cd desktop
npm run dev
```

This starts Electron, which auto-starts the FastAPI backend and Next.js frontend as subprocesses.

---

## 4 — Production build (Windows installer)

```bat
REM Build Next.js for production
cd frontend
npm run build
cd ..

REM Package everything into a Windows NSIS installer
cd desktop
npm run build:win
```

Output: `dist\AI Growth Operator Setup x.x.x.exe`

The installer:
- Bundles the Electron shell + license module
- Bundles the pre-built Next.js frontend
- Bundles the Python backend source
- Creates Start Menu + Desktop shortcuts

> **Note:** The packaged app expects Python to be installed on the target machine,
> or you must bundle a portable Python into `resources/python/`.
> For a fully self-contained build, use PyInstaller to freeze the backend first.

---

## 5 — License flow (end-user)

1. User installs and launches the app
2. If no valid lease → **Activation window** appears
3. User enters their license key → app calls `POST /api/license/validate` on the license server
4. Server returns a signed JWT lease (e.g. 7-day expiry)
5. Lease stored in Windows Credential Manager (via keytar)
6. App opens normally
7. Every 30 minutes: background poll to `POST /api/license/poll`
   - `CONTINUE` → nothing
   - `RENEW` → new lease stored
   - `BLOCK` → full-screen lock overlay shown immediately

---

## 6 — Offline behaviour

| Situation | Result |
|---|---|
| Internet down, lease valid | ✅ App works normally |
| Internet down, lease expired | ❌ Blocked — must reconnect to renew |
| Server sends BLOCK | ❌ Immediately locked |

---

## 7 — Security notes

- Lease JWT is stored in **Windows Credential Manager** (keytar), not a plain file
- The Gemini API key never leaves the license server
- All AI chat requests are routed: `Desktop → Local Backend → License Server → Gemini`
- JWT signature validation happens on the license server before any Gemini call
