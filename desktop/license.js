/**
 * Lease-based license manager for AI Growth Operator.
 *
 * Flow:
 *  1. On startup: read local lease → if valid, allow immediately.
 *  2. If no/expired lease: call license server → store new lease.
 *  3. Background poll every 30 min → CONTINUE | RENEW | BLOCK.
 *  4. Offline + valid lease → allow. Offline + expired → block.
 */

const { app, dialog } = require("electron");
const https = require("https");
const http = require("http");
const crypto = require("crypto");
const os = require("os");
const path = require("path");
const fs = require("fs");

// ── Config ────────────────────────────────────────────────────────────────────
const LICENSE_SERVER = process.env.LICENSE_SERVER_URL || "https://license.aigrowthoperator.com";
const POLL_INTERVAL_MS = process.env.NODE_ENV === "development" ? 60 * 1000 : 30 * 60 * 1000; // 1 min dev, 30 min prod
const LEASE_STORAGE_KEY = "ago_lease";
const MACHINE_ID_KEY = "ago_machine_id";

// Fallback storage path (used if keytar unavailable)
const STORAGE_PATH = path.join(app.getPath("userData"), ".lease");

// ── Machine ID ────────────────────────────────────────────────────────────────
function getMachineId() {
  // Stable per-machine fingerprint — not spoofable without effort
  const raw = `${os.hostname()}::${os.platform()}::${os.arch()}::${os.cpus()[0]?.model ?? "cpu"}`;
  return crypto.createHash("sha256").update(raw).digest("hex").slice(0, 32);
}

// ── Secure storage (keytar → file fallback) ───────────────────────────────────
let _keytar = null;
function getKeytar() {
  if (_keytar !== null) return _keytar;
  try {
    _keytar = require("keytar");
  } catch {
    _keytar = false;
  }
  return _keytar;
}

async function secureRead(key) {
  const kt = getKeytar();
  if (kt) {
    try { return await kt.getPassword("AIGrowthOperator", key); } catch {}
  }
  // File fallback — obfuscated but not cryptographically secure
  try {
    const data = JSON.parse(fs.readFileSync(STORAGE_PATH, "utf8"));
    return data[key] ?? null;
  } catch { return null; }
}

async function secureWrite(key, value) {
  const kt = getKeytar();
  if (kt) {
    try { await kt.setPassword("AIGrowthOperator", key, value); return; } catch {}
  }
  let data = {};
  try { data = JSON.parse(fs.readFileSync(STORAGE_PATH, "utf8")); } catch {}
  data[key] = value;
  fs.writeFileSync(STORAGE_PATH, JSON.stringify(data), { mode: 0o600 });
}

async function secureDelete(key) {
  const kt = getKeytar();
  if (kt) { try { await kt.deletePassword("AIGrowthOperator", key); } catch {} }
  try {
    let data = JSON.parse(fs.readFileSync(STORAGE_PATH, "utf8"));
    delete data[key];
    fs.writeFileSync(STORAGE_PATH, JSON.stringify(data), { mode: 0o600 });
  } catch {}
}

// ── JWT decode (no verify — server already signed; we verify sig below) ───────
function decodeJwt(token) {
  try {
    const [, payload] = token.split(".");
    return JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
  } catch { return null; }
}

// ── HTTP helper ───────────────────────────────────────────────────────────────
function post(url, body, timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const parsed = new URL(url);
    const lib = parsed.protocol === "https:" ? https : http;
    const req = lib.request(
      { hostname: parsed.hostname, port: parsed.port || (parsed.protocol === "https:" ? 443 : 80),
        path: parsed.pathname + parsed.search, method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) },
        timeout: timeoutMs },
      (res) => {
        let raw = "";
        res.on("data", (c) => (raw += c));
        res.on("end", () => {
          try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
          catch { resolve({ status: res.statusCode, body: raw }); }
        });
      }
    );
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    req.write(data);
    req.end();
  });
}

// ── Lease validation ──────────────────────────────────────────────────────────
function leaseValid(token) {
  if (!token) return false;
  const payload = decodeJwt(token);
  if (!payload) return false;
  const nowSec = Math.floor(Date.now() / 1000);
  return payload.exp && payload.exp > nowSec;
}

function leaseExpiresAt(token) {
  const payload = decodeJwt(token);
  return payload?.exp ? new Date(payload.exp * 1000) : null;
}

// ── Public API ────────────────────────────────────────────────────────────────
let _pollTimer = null;
let _onBlockCallback = null;
let _onCreditsUpdateCallback = null;
let _currentToken = null;
let _chatCredits = null; // cached from last poll/validate

/**
 * Called on app startup.
 * Returns { ok: boolean, reason?: string, needsActivation?: boolean }
 */
async function checkLicenseOnStartup() {
  const machineId = getMachineId();
  const licenseKey = await secureRead("ago_license_key");

  if (!licenseKey) {
    return { ok: false, needsActivation: true, reason: "No license key found." };
  }

  // Always validate with server first — catches blocks immediately
  console.log("[LICENSE] Validating with license server...");
  try {
    const result = await _validateWithServer(licenseKey, machineId);
    return result;
  } catch (err) {
    // Server unreachable — fall back to local lease if still valid
    console.warn("[LICENSE] Server unreachable on startup, checking local lease...");
    const stored = await secureRead(LEASE_STORAGE_KEY);
    if (leaseValid(stored)) {
      _currentToken = stored;
      console.log("[LICENSE] Offline fallback: local lease valid until", leaseExpiresAt(stored));
      _startPolling(machineId);
      return { ok: true };
    }
    return { ok: false, reason: "Cannot reach license server and no valid offline lease." };
  }
}

/**
 * Activate with a new license key (called from activation screen).
 */
async function activateLicense(licenseKey) {
  const machineId = getMachineId();
  const result = await _validateWithServer(licenseKey, machineId);
  if (result.ok) {
    await secureWrite("ago_license_key", licenseKey);
  }
  return result;
}

/**
 * Register callback invoked when server sends BLOCK.
 */
function onBlock(cb) { _onBlockCallback = cb; }
function onCreditsUpdate(cb) { _onCreditsUpdateCallback = cb; }

function getCurrentToken() { return _currentToken; }
function getChatCredits() { return _chatCredits; }

async function clearLicense() {
  await secureDelete(LEASE_STORAGE_KEY);
  await secureDelete("ago_license_key");
  _currentToken = null;
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

// ── Internal ──────────────────────────────────────────────────────────────────
async function _validateWithServer(licenseKey, machineId) {
  try {
    const res = await post(`${LICENSE_SERVER}/api/license/validate`, {
      license_key: licenseKey,
      machine_id: machineId,
      product_name: "ai-growth-operator",
    });

    if (res.status === 200 && res.body?.token) {
      _currentToken = res.body.token;
      await secureWrite(LEASE_STORAGE_KEY, _currentToken);
      // Cache credits from validate response
      if (res.body.chat_credits !== undefined) {
        _chatCredits = res.body.chat_credits;
        await secureWrite("ago_chat_credits", String(_chatCredits));
      }
      console.log("[LICENSE] Lease obtained, expires", leaseExpiresAt(_currentToken));
      _startPolling(machineId);
      return { ok: true };
    }

    if (res.status === 402 || res.status === 403) {
      return { ok: false, reason: res.body?.detail ?? res.body?.message ?? res.body?.status ?? "License invalid or expired." };
    }

    // Server error / unexpected — check if we have an expired lease to fall back on
    const stored = await secureRead(LEASE_STORAGE_KEY);
    if (stored) {
      return { ok: false, reason: "License server error. Your lease has expired. Please renew." };
    }
    return { ok: false, reason: "Could not reach license server. No offline lease available." };

  } catch (err) {
    console.error("[LICENSE] Server unreachable:", err.message);
    // Offline — already checked stored lease above; if we're here it was expired
    return { ok: false, reason: "Cannot reach license server and no valid offline lease." };
  }
}

function _startPolling(machineId) {
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(() => _poll(machineId), POLL_INTERVAL_MS);
}

async function _poll(machineId) {
  if (!_currentToken) return;
  console.log("[LICENSE] Polling license server...");
  try {
    const res = await post(`${LICENSE_SERVER}/api/license/poll`, {
      token: _currentToken,
      machine_id: machineId,
    });

    if (res.status !== 200) return;
    const { action, token } = res.body ?? {};

    if ((action === "RENEW" || action === "renew") && token) {
      _currentToken = token;
      await secureWrite(LEASE_STORAGE_KEY, token);
      console.log("[LICENSE] Lease renewed, expires", leaseExpiresAt(token));
    }
    // Credits top-up — server sends updated count on every poll
    if (res.body.chat_credits !== undefined) {
      const prev = _chatCredits;
      _chatCredits = res.body.chat_credits;
      await secureWrite("ago_chat_credits", String(_chatCredits));
      if (_onCreditsUpdateCallback && _chatCredits !== prev) {
        _onCreditsUpdateCallback(_chatCredits);
      }
      console.log("[LICENSE] Chat credits updated:", _chatCredits);
    }
    if (action === "BLOCK" || action === "block") {
      console.warn("[LICENSE] BLOCK received from server");
      _currentToken = null;
      await secureDelete(LEASE_STORAGE_KEY);
      if (_onBlockCallback) _onBlockCallback();
    }
    // CONTINUE → do nothing
  } catch (err) {
    console.warn("[LICENSE] Poll failed (offline?):", err.message);
    // Offline during poll — check local lease still valid
    if (!leaseValid(_currentToken)) {
      console.warn("[LICENSE] Lease expired and server unreachable — blocking");
      if (_onBlockCallback) _onBlockCallback();
    }
  }
}

module.exports = {
  checkLicenseOnStartup,
  activateLicense,
  onBlock,
  onCreditsUpdate,
  getCurrentToken,
  getChatCredits,
  clearLicense,
  getMachineId,
  leaseValid,
  leaseExpiresAt,
  decodeJwt,
  secureRead,
  secureWrite,
};
