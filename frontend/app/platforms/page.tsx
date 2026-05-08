"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Loader2, RefreshCw, Link2, CheckCircle, AlertCircle } from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const e = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((e as { detail?: string }).detail ?? "Request failed");
  }
  return res.json();
}

interface SyncResult {
  status: string; campaigns_added: number; total_rows: number;
  errors?: string[];
  aggregated: { total_spend: number; total_leads: number; blended_cpl: number; sources: string[] };
}

const PLATFORM_COLORS: Record<string, string> = {
  google_ads: "bg-blue-100 text-blue-700 border-blue-200",
  meta_ads: "bg-indigo-100 text-indigo-700 border-indigo-200",
};
const PLATFORM_LABELS: Record<string, string> = {
  google_ads: "🔵 Google Ads", meta_ads: "🔴 Meta Ads",
};

export default function PlatformsPage() {
  const [clients, setClients] = useState<{ id: number; name: string }[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null);
  const [googleId, setGoogleId] = useState("");
  const [metaId, setMetaId] = useState("");
  const [linking, setLinking] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    api.listClients().then(cs => {
      const valid = cs.filter(c => c.name.trim());
      setClients(valid.map(c => ({ id: c.id, name: c.name })));
      if (valid.length > 0) setSelectedClientId(valid[0].id);
    }).catch(() => {});
  }, []);

  // Pre-fill IDs when client changes
  useEffect(() => {
    if (!selectedClientId) return;
    req<{ google_ads_customer_id?: string; meta_ads_account_id?: string }>(
      `/api/clients/${selectedClientId}/platform-info`
    ).then(info => {
      if (info.google_ads_customer_id) setGoogleId(info.google_ads_customer_id);
      if (info.meta_ads_account_id) setMetaId(info.meta_ads_account_id);
    }).catch(() => {});
  }, [selectedClientId]);

  async function handleLink() {
    if (!selectedClientId) return;
    setLinking(true); setError(null);
    try {
      await req(`/api/clients/${selectedClientId}/link-platforms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          google_account_id: googleId || undefined,
          meta_account_id: metaId || undefined,
        }),
      });
      setSuccess("Platform IDs saved. Click Sync Now to pull campaign data.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to link");
    } finally { setLinking(false); }
  }

  async function handleSync() {
    if (!selectedClientId) return;
    setSyncing(true); setError(null); setSyncResult(null);
    try {
      const result = await req<SyncResult>(`/api/clients/${selectedClientId}/sync-platforms`, { method: "POST" });
      setSyncResult(result);
      if (result.errors && result.errors.length > 0) {
        setError(result.errors.join(" | "));
      } else {
        setSuccess(`Synced ${result.total_rows} rows from ${result.aggregated.sources.join(" + ")}.`);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Sync failed");
    } finally { setSyncing(false); }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Platform Connections</h1>
        <p className="text-sm text-gray-500 mt-1">Link Google Ads and Meta Ads accounts to sync campaign data automatically</p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
        <p className="font-semibold mb-1">How this works</p>
        <ol className="list-decimal list-inside space-y-1 text-blue-700">
          <li>Select a client and enter their Google Ads Customer ID and/or Meta Ads Account ID</li>
          <li>Click <strong>Save IDs</strong> — this stores the account IDs against the client</li>
          <li>Click <strong>Sync Now</strong> — pulls the last 30 days of campaign data into the database</li>
          <li>Go to <strong>Dashboard</strong>, select the client — data loads automatically</li>
        </ol>
        <p className="mt-2 text-xs text-blue-600">
          Note: Real API sync requires OAuth access tokens. Until OAuth is connected, use CSV upload on the Dashboard.
        </p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg flex items-center gap-2"><AlertCircle size={14} /> {error}</div>}
      {success && <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm px-4 py-3 rounded-lg flex items-center gap-2"><CheckCircle size={14} /> {success}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Step 1: Link */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold">1</span>
            <h2 className="text-sm font-semibold text-gray-800">Save Platform Account IDs</h2>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Client</label>
            <select value={selectedClientId ?? ""} onChange={e => setSelectedClientId(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
              {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              🔵 Google Ads Customer ID
              <a href="https://support.google.com/google-ads/answer/1704344" target="_blank" rel="noreferrer" className="ml-1 text-indigo-500 hover:underline">Where to find?</a>
            </label>
            <input value={googleId} onChange={e => setGoogleId(e.target.value)}
              placeholder="e.g. 1234567890"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400" />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              🔴 Meta Ads Account ID
              <a href="https://www.facebook.com/business/help/1492627900875762" target="_blank" rel="noreferrer" className="ml-1 text-indigo-500 hover:underline">Where to find?</a>
            </label>
            <input value={metaId} onChange={e => setMetaId(e.target.value)}
              placeholder="e.g. act_111222333"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400" />
          </div>

          <button onClick={handleLink} disabled={linking || (!googleId && !metaId)}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors">
            {linking ? <Loader2 size={14} className="animate-spin" /> : <Link2 size={14} />}
            {linking ? "Saving…" : "Save IDs"}
          </button>
        </div>

        {/* Step 2: Sync */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold">2</span>
            <h2 className="text-sm font-semibold text-gray-800">Sync Campaign Data</h2>
          </div>
          <p className="text-xs text-gray-500">Pulls the last 30 days of campaign data from all linked platforms and saves it to the database. Run this daily to keep data fresh.</p>

          <button onClick={handleSync} disabled={syncing || !selectedClientId}
            className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors">
            {syncing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            {syncing ? "Syncing…" : "Sync Now"}
          </button>

          {syncResult && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-2 text-emerald-700 font-semibold text-sm">
                <CheckCircle size={15} /> Sync complete
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Total Spend", value: `$${syncResult.aggregated.total_spend.toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
                  { label: "Total Leads", value: syncResult.aggregated.total_leads.toLocaleString() },
                  { label: "Blended CPL", value: `$${syncResult.aggregated.blended_cpl}` },
                  { label: "Rows Synced", value: syncResult.total_rows.toLocaleString() },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-white rounded-lg p-3 border border-emerald-100">
                    <div className="text-xs text-gray-500">{label}</div>
                    <div className="text-sm font-bold text-gray-900">{value}</div>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                {syncResult.aggregated.sources.map(s => (
                  <span key={s} className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${PLATFORM_COLORS[s] ?? "bg-gray-100 text-gray-700"}`}>
                    {PLATFORM_LABELS[s] ?? s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
