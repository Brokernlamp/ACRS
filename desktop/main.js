const { app, BrowserWindow, ipcMain, dialog, shell } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");
const https = require("https");
const fs = require("fs");

// Load desktop/.env before anything reads process.env
// (only in dev — packaged builds use system env / installer config)
if (!app.isPackaged) {
  const envPath = path.join(__dirname, ".env");
  if (fs.existsSync(envPath)) {
    fs.readFileSync(envPath, "utf8")
      .split("\n")
      .forEach((line) => {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) return;
        const eq = trimmed.indexOf("=");
        if (eq === -1) return;
        const key = trimmed.slice(0, eq).trim();
        const val = trimmed.slice(eq + 1).trim();
        if (key && !(key in process.env)) process.env[key] = val;
      });
    console.log("[DESKTOP] Loaded desktop/.env");
  }
}

const license = require("./license");

// ── Config ────────────────────────────────────────────────────────────────────
const CONFIG = {
  backendPort: 8000,
  frontendPort: 3000,
  backendUrl: "http://localhost:8000",
  frontendUrl: "http://localhost:3000",
  healthEndpoint: "/api/health",
  backendStartTimeout: 30000,
  frontendStartTimeout: 45000,
};

let mainWindow = null;
let backendProcess = null;
let frontendProcess = null;
let splashWindow = null;
let activationWindow = null;

// ── Paths ─────────────────────────────────────────────────────────────────────
function getRootDir() {
  return app.isPackaged ? path.join(process.resourcesPath, "app") : path.join(__dirname, "..");
}

function getPythonPath() {
  const root = getRootDir();
  if (process.platform === "win32") {
    return app.isPackaged
      ? path.join(process.resourcesPath, "python", "python.exe")
      : path.join(root, "backend", ".venv", "Scripts", "python.exe");
  }
  return app.isPackaged
    ? path.join(process.resourcesPath, "python", "bin", "python3")
    : path.join(root, "backend", ".venv", "bin", "python3");
}

// ── Internet check ────────────────────────────────────────────────────────────
function checkInternet() {
  return new Promise((resolve) => {
    const req = https.get("https://www.google.com", { timeout: 5000 }, (res) => {
      resolve(res.statusCode < 500);
    });
    req.on("error", () => resolve(false));
    req.on("timeout", () => { req.destroy(); resolve(false); });
  });
}

// ── Wait for HTTP endpoint ────────────────────────────────────────────────────
function waitForHttp(url, timeoutMs) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      http.get(url, (res) => {
        if (res.statusCode < 500) return resolve(true);
        retry();
      }).on("error", retry);
    };
    const retry = () => {
      if (Date.now() - start > timeoutMs) return reject(new Error(`Timeout: ${url}`));
      setTimeout(check, 1000);
    };
    check();
  });
}

// ── Splash window ─────────────────────────────────────────────────────────────
function createSplash() {
  splashWindow = new BrowserWindow({
    width: 480, height: 300,
    frame: false, transparent: true, alwaysOnTop: true,
    webPreferences: { nodeIntegration: false },
  });
  splashWindow.loadFile(path.join(__dirname, "splash.html"));
}

function updateSplash(message) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.executeJavaScript(
      `document.getElementById('status') && (document.getElementById('status').textContent = ${JSON.stringify(message)})`
    );
  }
}

function closeSplash() {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close();
    splashWindow = null;
  }
}

// ── Activation window ─────────────────────────────────────────────────────────
function createActivationWindow() {
  activationWindow = new BrowserWindow({
    width: 520, height: 480,
    resizable: false,
    frame: true,
    title: "Activate AI Growth Operator",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, "assets", "icon.png"),
  });
  // Load the activation page from the running Next.js frontend
  activationWindow.loadURL(`${CONFIG.frontendUrl}/activate`);
  activationWindow.on("closed", () => { activationWindow = null; });
}

// ── Main window ───────────────────────────────────────────────────────────────
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400, height: 900,
    minWidth: 1024, minHeight: 700,
    show: false,
    titleBarStyle: "hiddenInset",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, "assets", "icon.png"),
    title: "AI Growth Operator",
  });

  mainWindow.loadURL(CONFIG.frontendUrl);

  mainWindow.once("ready-to-show", () => {
    closeSplash();
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on("closed", () => { mainWindow = null; });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http")) shell.openExternal(url);
    return { action: "deny" };
  });
}

// ── Block handler — called when server sends BLOCK ────────────────────────────
function handleBlock() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    // Inject a full-screen block overlay into the running app
    mainWindow.webContents.executeJavaScript(`
      (function() {
        const el = document.getElementById('__license_block__');
        if (el) return;
        const div = document.createElement('div');
        div.id = '__license_block__';
        div.style.cssText = 'position:fixed;inset:0;z-index:99999;background:#0F172A;display:flex;flex-direction:column;align-items:center;justify-content:center;color:white;font-family:system-ui';
        div.innerHTML = '<div style="font-size:48px;margin-bottom:16px">🔒</div><h1 style="font-size:22px;font-weight:700;margin-bottom:8px">Subscription Ended</h1><p style="color:#94A3B8;font-size:14px;text-align:center;max-width:320px">Your license has been deactivated by the server.<br>Please renew your subscription to continue.</p>';
        document.body.appendChild(div);
      })();
    `);
  }
  dialog.showMessageBox({
    type: "warning",
    title: "License Deactivated",
    message: "Your subscription has been deactivated by the license server.\n\nPlease renew your subscription to continue using AI Growth Operator.",
    buttons: ["OK"],
  });
}

// ── Start backend ─────────────────────────────────────────────────────────────
function startBackend() {
  const root = getRootDir();
  const python = getPythonPath();
  const backendDir = path.join(root, "backend");

  backendProcess = spawn(
    python,
    ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", String(CONFIG.backendPort), "--log-level", "warning"],
    {
      cwd: backendDir,
      env: { ...process.env, PYTHONPATH: backendDir, PYTHONUNBUFFERED: "1" },
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  backendProcess.stdout.on("data", (d) => console.log("[BACKEND]", d.toString().trim()));
  backendProcess.stderr.on("data", (d) => console.error("[BACKEND ERR]", d.toString().trim()));
  backendProcess.on("exit", (code) => { console.log("[DESKTOP] Backend exited:", code); backendProcess = null; });
}

// ── Start frontend ────────────────────────────────────────────────────────────
function startFrontend() {
  const root = getRootDir();
  const frontendDir = path.join(root, "frontend");
  const script = app.isPackaged ? "start" : "dev";

  frontendProcess = spawn("npm", ["run", script], {
    cwd: frontendDir,
    env: { ...process.env, NEXT_PUBLIC_API_URL: CONFIG.backendUrl, PORT: String(CONFIG.frontendPort) },
    stdio: ["ignore", "pipe", "pipe"],
    shell: process.platform === "win32",
  });

  frontendProcess.stdout.on("data", (d) => console.log("[FRONTEND]", d.toString().trim()));
  frontendProcess.stderr.on("data", (d) => console.error("[FRONTEND ERR]", d.toString().trim()));
  frontendProcess.on("exit", (code) => { console.log("[DESKTOP] Frontend exited:", code); frontendProcess = null; });
}

// ── Cleanup ───────────────────────────────────────────────────────────────────
function killAll() {
  if (backendProcess) { backendProcess.kill("SIGTERM"); backendProcess = null; }
  if (frontendProcess) { frontendProcess.kill("SIGTERM"); frontendProcess = null; }
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  createSplash();

  // 1. Start backend + frontend first (needed for activation page too)
  updateSplash("Starting AI engine...");
  startBackend();
  try {
    await waitForHttp(`${CONFIG.backendUrl}${CONFIG.healthEndpoint}`, CONFIG.backendStartTimeout);
  } catch {
    closeSplash();
    dialog.showErrorBox("Startup Error", "Failed to start the AI backend. Please restart the app.");
    killAll(); app.quit(); return;
  }

  updateSplash("Loading interface...");
  startFrontend();
  try {
    await waitForHttp(CONFIG.frontendUrl, CONFIG.frontendStartTimeout);
  } catch {
    closeSplash();
    dialog.showErrorBox("Startup Error", "Failed to start the interface. Please restart the app.");
    killAll(); app.quit(); return;
  }

  // 2. License check
  updateSplash("Validating license...");
  license.onBlock(handleBlock);
  license.onCreditsUpdate((credits) => {
    // Push updated credits to the frontend without requiring a page reload
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send("credits:updated", credits);
    }
  });

  // Dev convenience: if LICENSE_KEY is set in env, always write it to secure storage
  // (overwrites so key changes in .env take effect immediately)
  if (process.env.LICENSE_KEY && process.env.LICENSE_KEY !== "<paste key from admin panel here>") {
    await license.secureWrite("ago_license_key", process.env.LICENSE_KEY);
    console.log("[DESKTOP] License key loaded from env");
  }

  const licenseResult = await license.checkLicenseOnStartup();

  if (licenseResult.needsActivation) {
    // Show activation window — user must enter license key
    closeSplash();
    createActivationWindow();
    return; // main window opens after successful activation via IPC
  }

  if (!licenseResult.ok) {
    closeSplash();
    dialog.showErrorBox("License Error", licenseResult.reason ?? "License validation failed.");
    killAll(); app.quit(); return;
  }

  // 3. License valid — open main app
  createMainWindow();
});

app.on("window-all-closed", () => { killAll(); app.quit(); });
app.on("before-quit", killAll);

// ── IPC handlers ──────────────────────────────────────────────────────────────
ipcMain.handle("get-config", () => CONFIG);
ipcMain.handle("check-internet", () => checkInternet());
ipcMain.handle("open-external", (_, url) => shell.openExternal(url));

// License IPC
ipcMain.handle("license:activate", async (_, licenseKey) => {
  const result = await license.activateLicense(licenseKey.trim());
  if (result.ok && activationWindow && !activationWindow.isDestroyed()) {
    activationWindow.close();
    createMainWindow();
  }
  return result;
});

ipcMain.handle("license:status", async () => {
  const token = license.getCurrentToken();
  if (!token) return { valid: false };
  const payload = license.decodeJwt(token);
  return {
    valid: license.leaseValid(token),
    expiresAt: license.leaseExpiresAt(token)?.toISOString() ?? null,
    machineId: license.getMachineId(),
    email: payload?.email ?? null,
    plan: payload?.plan ?? null,
  };
});

ipcMain.handle("license:clear", async () => {
  await license.clearLicense();
  return { ok: true };
});

ipcMain.handle("license:get-machine-id", () => license.getMachineId());
ipcMain.handle("license:get-credits", () => license.getChatCredits());
