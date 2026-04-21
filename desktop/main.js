const { app, BrowserWindow, ipcMain, dialog, shell } = require("electron");
const { spawn, execSync } = require("child_process");
const path = require("path");
const http = require("http");
const https = require("https");
const fs = require("fs");

// ── Config ────────────────────────────────────────────────────────────────────
const CONFIG = {
  backendPort: 8000,
  frontendPort: 3000,
  backendUrl: "http://localhost:8000",
  frontendUrl: "http://localhost:3000",
  healthEndpoint: "/api/health",
  internetCheckHost: "8.8.8.8",   // Google DNS — reliable ping target
  backendStartTimeout: 30000,      // 30s max wait for backend
  frontendStartTimeout: 45000,     // 45s max wait for Next.js
};

let mainWindow = null;
let backendProcess = null;
let frontendProcess = null;
let splashWindow = null;

// ── Paths ─────────────────────────────────────────────────────────────────────
function getRootDir() {
  // In production (packaged), resources are in process.resourcesPath
  // In dev, go up from desktop/
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "app");
  }
  return path.join(__dirname, "..");
}

function getPythonPath() {
  const root = getRootDir();
  if (process.platform === "win32") {
    // Packaged: bundled Python; Dev: venv
    if (app.isPackaged) {
      return path.join(process.resourcesPath, "python", "python.exe");
    }
    return path.join(root, "backend", ".venv", "Scripts", "python.exe");
  }
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "python", "bin", "python3");
  }
  return path.join(root, "backend", ".venv", "bin", "python3");
}

function getNodePath() {
  if (app.isPackaged) {
    return process.platform === "win32"
      ? path.join(process.resourcesPath, "node", "node.exe")
      : path.join(process.resourcesPath, "node", "bin", "node");
  }
  return process.execPath; // current Node binary in dev
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
      if (Date.now() - start > timeoutMs) return reject(new Error(`Timeout waiting for ${url}`));
      setTimeout(check, 1000);
    };
    check();
  });
}

// ── Splash window ─────────────────────────────────────────────────────────────
function createSplash() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
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

// ── Main window ───────────────────────────────────────────────────────────────
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
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
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on("closed", () => { mainWindow = null; });

  // Open external links in browser, not Electron
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http")) shell.openExternal(url);
    return { action: "deny" };
  });
}

// ── Start backend ─────────────────────────────────────────────────────────────
function startBackend() {
  const root = getRootDir();
  const python = getPythonPath();
  const backendDir = path.join(root, "backend");

  console.log("[DESKTOP] Starting backend:", python);

  backendProcess = spawn(python, ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", String(CONFIG.backendPort), "--log-level", "warning"], {
    cwd: backendDir,
    env: {
      ...process.env,
      PYTHONPATH: backendDir,
      PYTHONUNBUFFERED: "1",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  backendProcess.stdout.on("data", (d) => console.log("[BACKEND]", d.toString().trim()));
  backendProcess.stderr.on("data", (d) => console.error("[BACKEND ERR]", d.toString().trim()));
  backendProcess.on("exit", (code) => {
    console.log("[DESKTOP] Backend exited with code", code);
    backendProcess = null;
  });
}

// ── Start frontend ────────────────────────────────────────────────────────────
function startFrontend() {
  const root = getRootDir();
  const frontendDir = path.join(root, "frontend");

  // In production use `next start`, in dev use `next dev`
  const script = app.isPackaged ? "start" : "dev";
  console.log("[DESKTOP] Starting frontend:", script);

  frontendProcess = spawn("npm", ["run", script], {
    cwd: frontendDir,
    env: {
      ...process.env,
      NEXT_PUBLIC_API_URL: CONFIG.backendUrl,
      PORT: String(CONFIG.frontendPort),
    },
    stdio: ["ignore", "pipe", "pipe"],
    shell: process.platform === "win32",
  });

  frontendProcess.stdout.on("data", (d) => console.log("[FRONTEND]", d.toString().trim()));
  frontendProcess.stderr.on("data", (d) => console.error("[FRONTEND ERR]", d.toString().trim()));
  frontendProcess.on("exit", (code) => {
    console.log("[DESKTOP] Frontend exited with code", code);
    frontendProcess = null;
  });
}

// ── Cleanup ───────────────────────────────────────────────────────────────────
function killAll() {
  console.log("[DESKTOP] Shutting down...");
  if (backendProcess) {
    backendProcess.kill("SIGTERM");
    backendProcess = null;
  }
  if (frontendProcess) {
    frontendProcess.kill("SIGTERM");
    frontendProcess = null;
  }
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  createSplash();

  // 1. Internet check
  updateSplash("Checking internet connection...");
  const online = await checkInternet();
  if (!online) {
    if (splashWindow) splashWindow.close();
    dialog.showErrorBox(
      "No Internet Connection",
      "AI Growth Operator requires an internet connection to function.\n\nPlease connect to the internet and try again."
    );
    app.quit();
    return;
  }

  // 2. Start backend
  updateSplash("Starting AI engine...");
  startBackend();
  try {
    await waitForHttp(`${CONFIG.backendUrl}${CONFIG.healthEndpoint}`, CONFIG.backendStartTimeout);
    console.log("[DESKTOP] Backend ready");
  } catch (e) {
    dialog.showErrorBox("Startup Error", "Failed to start the AI backend. Please try restarting the app.");
    killAll();
    app.quit();
    return;
  }

  // 3. Start frontend
  updateSplash("Loading interface...");
  startFrontend();
  try {
    await waitForHttp(CONFIG.frontendUrl, CONFIG.frontendStartTimeout);
    console.log("[DESKTOP] Frontend ready");
  } catch (e) {
    dialog.showErrorBox("Startup Error", "Failed to start the interface. Please try restarting the app.");
    killAll();
    app.quit();
    return;
  }

  // 4. Open main window
  createMainWindow();
});

app.on("window-all-closed", () => {
  killAll();
  app.quit();
});

app.on("before-quit", killAll);

// IPC handlers
ipcMain.handle("get-config", () => CONFIG);
ipcMain.handle("check-internet", () => checkInternet());
ipcMain.handle("open-external", (_, url) => shell.openExternal(url));
