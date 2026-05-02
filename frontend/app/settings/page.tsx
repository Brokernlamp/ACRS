"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Save, Loader2, Download, Eye, EyeOff, CheckCircle, AlertCircle, Key, Database, Cpu, Zap } from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Settings {
  groq_api_key_set: boolean;
  groq_api_key_preview: string;
  gemini_api_key_set: boolean;
  gemini_api_key_preview: string;
  active_provider: string;
  active_model: string;
  database_url: string;
}

async function saveKey(payload: object) {
  const res = await fetch(`${BASE}/api/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to save");
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [groqKey, setGroqKey] = useState("");
  const [geminiKey, setGeminiKey] = useState("");
  const [showGroq, setShowGroq] = useState(false);
  const [showGemini, setShowGemini] = useState(false);
  const [saving, setSaving] = useState<"groq" | "gemini" | null>(null);
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);

  async function load() {
    try {
      const s = await fetch(`${BASE}/api/settings`).then(r => r.json());
      setSettings(s);
    } catch {}
  }

  useEffect(() => { load(); }, []);

  async function handleSave(provider: "groq" | "gemini") {
    const key = provider === "groq" ? groqKey.trim() : geminiKey.trim();
    if (!key) return setStatus({ ok: false, msg: "Enter a key first." });
    setSaving(provider); setStatus(null);
    try {
      const payload = provider === "groq"
        ? { groq_api_key: key }
        : { gemini_api_key: key };
      await saveKey(payload);
      await load();
      provider === "groq" ? setGroqKey("") : setGeminiKey("");
      setStatus({ ok: true, msg: `${provider === "groq" ? "Groq" : "Gemini"} API key saved.` });
    } catch (e: unknown) {
      setStatus({ ok: false, msg: e instanceof Error ? e.message : "Failed to save" });
    } finally { setSaving(null); }
  }

  const PROVIDER_LABELS: Record<string, string> = {
    groq: "Groq (llama-3.1-8b-instant)",
    gemini: "Google Gemini",
    none: "Not configured",
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Configure API keys and download sample data</p>
      </div>

      {/* Active provider banner */}
      {settings && (
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm font-medium ${
          settings.active_provider !== "none"
            ? "bg-emerald-50 border-emerald-200 text-emerald-800"
            : "bg-amber-50 border-amber-200 text-amber-800"
        }`}>
          <Zap size={15} />
          {settings.active_provider !== "none"
            ? <>Active AI provider: <strong>{PROVIDER_LABELS[settings.active_provider]}</strong> — model: <code className="bg-white/60 px-1.5 py-0.5 rounded text-xs">{settings.active_model}</code></>
            : "No AI provider configured. Add a Groq or Gemini API key below."}
        </div>
      )}

      {status && (
        <div className={`flex items-center gap-2 text-sm px-4 py-3 rounded-lg border ${status.ok ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-red-50 border-red-200 text-red-800"}`}>
          {status.ok ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
          {status.msg}
        </div>
      )}

      {/* Groq API Key — primary */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 bg-gray-50">
          <Key size={16} className="text-indigo-600" />
          <div>
            <h2 className="text-sm font-semibold text-gray-800">Groq API Key <span className="text-xs font-normal text-indigo-600 ml-1">Recommended — Free, fastest</span></h2>
            <p className="text-xs text-gray-500 mt-0.5">14,400 free requests/day · <a href="https://console.groq.com" target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">console.groq.com</a></p>
          </div>
          <div className="ml-auto">
            {settings?.groq_api_key_set
              ? <span className="flex items-center gap-1 text-xs text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full font-medium"><CheckCircle size={11} /> Configured</span>
              : <span className="flex items-center gap-1 text-xs text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full font-medium"><AlertCircle size={11} /> Not set</span>}
          </div>
        </div>
        <div className="p-5 space-y-3">
          {settings?.groq_api_key_set && (
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5">
              <span className="text-xs text-slate-500 font-medium">Current:</span>
              <span className="text-sm font-mono text-slate-700">{settings.groq_api_key_preview}</span>
            </div>
          )}
          <div className="relative">
            <input type={showGroq ? "text" : "password"} value={groqKey}
              onChange={e => setGroqKey(e.target.value)}
              placeholder="gsk_..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 pr-10 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            <button onClick={() => setShowGroq(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              {showGroq ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>
          <button onClick={() => handleSave("groq")} disabled={saving !== null || !groqKey.trim()}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
            {saving === "groq" ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            {saving === "groq" ? "Saving…" : "Save Groq Key"}
          </button>
        </div>
      </div>

      {/* Gemini API Key — fallback */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 bg-gray-50">
          <Key size={16} className="text-violet-600" />
          <div>
            <h2 className="text-sm font-semibold text-gray-800">Google Gemini API Key <span className="text-xs font-normal text-gray-400 ml-1">Fallback</span></h2>
            <p className="text-xs text-gray-500 mt-0.5">Used if no Groq key is set · <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">makersuite.google.com</a></p>
          </div>
          <div className="ml-auto">
            {settings?.gemini_api_key_set
              ? <span className="flex items-center gap-1 text-xs text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full font-medium"><CheckCircle size={11} /> Configured</span>
              : <span className="flex items-center gap-1 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full font-medium">Not set</span>}
          </div>
        </div>
        <div className="p-5 space-y-3">
          {settings?.gemini_api_key_set && (
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5">
              <span className="text-xs text-slate-500 font-medium">Current:</span>
              <span className="text-sm font-mono text-slate-700">{settings.gemini_api_key_preview}</span>
            </div>
          )}
          <div className="relative">
            <input type={showGemini ? "text" : "password"} value={geminiKey}
              onChange={e => setGeminiKey(e.target.value)}
              placeholder="AIza..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 pr-10 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            <button onClick={() => setShowGemini(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              {showGemini ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>
          <button onClick={() => handleSave("gemini")} disabled={saving !== null || !geminiKey.trim()}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-40 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
            {saving === "gemini" ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            {saving === "gemini" ? "Saving…" : "Save Gemini Key"}
          </button>
        </div>
      </div>

      {/* Model + DB info */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 bg-gray-50">
          <Cpu size={16} className="text-indigo-600" />
          <h2 className="text-sm font-semibold text-gray-800">System Info</h2>
        </div>
        <div className="p-5 divide-y divide-gray-100">
          <div className="flex items-center justify-between py-2.5">
            <span className="text-sm text-gray-600">Active provider</span>
            <span className="text-sm font-semibold text-gray-900 capitalize">{settings?.active_provider ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between py-2.5">
            <span className="text-sm text-gray-600">Active model</span>
            <span className="text-sm font-mono text-gray-900">{settings?.active_model ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between py-2.5">
            <span className="text-sm text-gray-600">Database</span>
            <span className="text-sm font-mono text-gray-700 truncate max-w-xs">{settings?.database_url ?? "—"}</span>
          </div>
        </div>
      </div>

      {/* Sample data */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 bg-gray-50">
          <Download size={16} className="text-indigo-600" />
          <h2 className="text-sm font-semibold text-gray-800">Sample Data</h2>
        </div>
        <div className="p-5 space-y-3">
          <p className="text-sm text-gray-600">60-day, 4-campaign dataset with impressions, clicks, spend, leads, and revenue.</p>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs font-mono text-slate-600">
            date, campaign, impressions, clicks, spend, leads, revenue<br />
            2024-01-01, Google Search, 24500, 312, 487.20, 28, 3640.00<br />
            <span className="text-slate-400">… 60 days × 4 campaigns = 240 rows</span>
          </div>
          <a href={api.sampleDataUrl()} download="sample_campaign_data.csv"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
            <Download size={14} /> Download Sample CSV
          </a>
        </div>
      </div>
    </div>
  );
}
