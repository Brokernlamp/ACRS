"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Save, Loader2, Download, Eye, EyeOff, CheckCircle, AlertCircle, Key, Database, Cpu } from "lucide-react";

interface Settings {
  gemini_api_key_set: boolean;
  gemini_api_key_preview: string;
  gemini_model: string;
  database_url: string;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);

  useEffect(() => {
    api.getSettings().then(s => { setSettings(s); }).catch(() => {});
  }, []);

  async function handleSave() {
    if (!apiKey.trim()) return setStatus({ ok: false, msg: "Enter an API key first." });
    setSaving(true); setStatus(null);
    try {
      await api.saveSettings(apiKey.trim());
      const updated = await api.getSettings();
      setSettings(updated);
      setApiKey("");
      setStatus({ ok: true, msg: "API key saved. Chatbot will use it on the next message." });
    } catch (e: unknown) {
      setStatus({ ok: false, msg: e instanceof Error ? e.message : "Failed to save" });
    } finally { setSaving(false); }
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Configure API keys and download sample data</p>
      </div>

      {/* Gemini API Key */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 bg-gray-50">
          <Key size={16} className="text-indigo-600" />
          <h2 className="text-sm font-semibold text-gray-800">Google Gemini API Key</h2>
          {settings?.gemini_api_key_set
            ? <span className="ml-auto flex items-center gap-1 text-xs text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full font-medium"><CheckCircle size={11} /> Configured</span>
            : <span className="ml-auto flex items-center gap-1 text-xs text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full font-medium"><AlertCircle size={11} /> Not set</span>
          }
        </div>
        <div className="p-5 space-y-4">
          {settings?.gemini_api_key_set && (
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5">
              <span className="text-xs text-slate-500 font-medium">Current key:</span>
              <span className="text-sm font-mono text-slate-700">{settings.gemini_api_key_preview}</span>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1.5">
              {settings?.gemini_api_key_set ? "Replace API Key" : "Enter API Key"}
            </label>
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                placeholder="AIza..."
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 pr-10 text-sm font-mono text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <button onClick={() => setShowKey(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1.5">
              Get your key at{" "}
              <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noreferrer"
                className="text-indigo-600 hover:underline font-medium">
                makersuite.google.com
              </a>
            </p>
          </div>
          <button onClick={handleSave} disabled={saving || !apiKey.trim()}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            {saving ? "Saving…" : "Save API Key"}
          </button>
          {status && (
            <div className={`flex items-center gap-2 text-sm px-4 py-3 rounded-lg border ${status.ok ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-red-50 border-red-200 text-red-800"}`}>
              {status.ok ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
              {status.msg}
            </div>
          )}
        </div>
      </div>

      {/* Model info */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 bg-gray-50">
          <Cpu size={16} className="text-indigo-600" />
          <h2 className="text-sm font-semibold text-gray-800">AI Model</h2>
        </div>
        <div className="p-5">
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Active model</span>
            <span className="text-sm font-semibold text-gray-900 font-mono">{settings?.gemini_model ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-gray-600">Provider</span>
            <span className="text-sm font-semibold text-gray-900">Google Gemini</span>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            To change the model, edit <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">MODEL</code> in <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">backend/chatbot.py</code>.
          </p>
        </div>
      </div>

      {/* Database */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 bg-gray-50">
          <Database size={16} className="text-indigo-600" />
          <h2 className="text-sm font-semibold text-gray-800">Database</h2>
        </div>
        <div className="p-5">
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-gray-600">Connection</span>
            <span className="text-sm font-mono text-gray-900 truncate max-w-xs">{settings?.database_url ?? "—"}</span>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Change <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">DATABASE_URL</code> in <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">backend/.env</code> to switch to PostgreSQL for production.
          </p>
        </div>
      </div>

      {/* Sample data */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 bg-gray-50">
          <Download size={16} className="text-indigo-600" />
          <h2 className="text-sm font-semibold text-gray-800">Sample Data</h2>
        </div>
        <div className="p-5 space-y-3">
          <p className="text-sm text-gray-600">
            Download a realistic 60-day, 4-campaign dataset with impressions, clicks, spend, leads, and revenue. Use it to explore all features before connecting real data.
          </p>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs font-mono text-slate-600">
            date, campaign, impressions, clicks, spend, leads, revenue<br />
            2024-01-01, Google Search, 24500, 312, 487.20, 28, 3640.00<br />
            2024-01-01, Meta Retargeting, 18200, 198, 231.50, 19, 2090.00<br />
            <span className="text-slate-400">… 60 days × 4 campaigns = 240 rows</span>
          </div>
          <a
            href={api.sampleDataUrl()}
            download="sample_campaign_data.csv"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors"
          >
            <Download size={14} />
            Download Sample CSV
          </a>
        </div>
      </div>
    </div>
  );
}
