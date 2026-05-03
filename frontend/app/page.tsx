"use client";
import { useEffect, useRef, useState } from "react";
import { api, Client } from "@/lib/api";
import { useAppState } from "@/lib/store";
import KpiCards from "@/components/KpiCards";
import PlotlyChart from "@/components/PlotlyChart";
import StatusBanner from "@/components/StatusBanner";
import {
  RefreshCw, Loader2, Download, AlertTriangle,
  Upload, Globe, ChevronDown, Plus, X,
} from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const e = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((e as { detail?: string }).detail ?? "Request failed");
  }
  return res.json();
}

type DataSource = "csv" | "platforms" | null;

export default function DashboardPage() {
  const { data, setData, clientId, setClientId, clientName, setClientName, setLoading, loading, setError, clearData } = useAppState();

  const [clients, setClients] = useState<Client[]>([]);
  const [dataSource, setDataSource] = useState<DataSource>("csv"); // default open
  const [showNewClient, setShowNewClient] = useState(false);
  const [newClientName, setNewClientName] = useState("");

  // CSV state
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Platform sync state
  const [googleId, setGoogleId] = useState("");
  const [metaId, setMetaId] = useState("");
  const [syncing, setSyncing] = useState(false);

  // Date filter
  const today = new Date().toISOString().slice(0, 10);
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
  const [startDate, setStartDate] = useState(monthAgo);
  const [endDate, setEndDate] = useState(today);
  const [comparison, setComparison] = useState("None");

  // Load clients on mount
  useEffect(() => {
    api.listClients().then(cs => {
      const valid = cs.filter(c => c.name.trim());
      setClients(valid);
      // Auto-select first client if none selected
      if (!clientId && valid.length > 0) {
        setClientId(valid[0].id);
        setClientName(valid[0].name);
      }
    }).catch(() => {});
  }, []);

  // When client changes, pre-fill platform IDs if already linked
  useEffect(() => {
    if (!clientId) return;
    // Try to load existing data for this client
    req<{ google_ads_customer_id?: string; meta_ads_account_id?: string }>(
      `/api/clients/${clientId}/platform-info`
    ).then(info => {
      if (info.google_ads_customer_id) setGoogleId(info.google_ads_customer_id);
      if (info.meta_ads_account_id) setMetaId(info.meta_ads_account_id);
    }).catch(() => {});
  }, [clientId]);

  async function handleCreateClient() {
    if (!newClientName.trim()) return;
    try {
      const c = await api.addClient({ name: newClientName.trim() });
      const updated = await api.listClients();
      setClients(updated.filter(cl => cl.name.trim()));
      setClientId(c.id);
      setClientName(c.name);
      setNewClientName("");
      setShowNewClient(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create client");
    }
  }

  async function handleCSVUpload() {
    if (!file) return setError("Please select a CSV file.");
    if (!clientName.trim()) return setError("Please select or create a client first.");
    setLoading(true); setError(null);
    try {
      const result = await api.upload(file, clientName.trim());
      setData(result);
      // Refresh client list to update stats
      api.listClients().then(cs => setClients(cs.filter(c => c.name.trim()))).catch(() => {});
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally { setLoading(false); }
  }

  async function handlePlatformSync() {
    if (!clientId) return setError("Select a client first.");
    if (!googleId && !metaId) return setError("Enter at least one platform account ID.");
    setSyncing(true); setError(null);
    try {
      // Link platforms first
      await req(`/api/clients/${clientId}/link-platforms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          google_account_id: googleId || undefined,
          meta_account_id: metaId || undefined,
        }),
      });
      // Sync data
      await req(`/api/clients/${clientId}/sync-platforms`, { method: "POST" });
      // Now load into dashboard via refresh
      const result = await api.refresh(startDate, endDate, "None");
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Sync failed");
    } finally { setSyncing(false); }
  }

  async function handleRefresh() {
    setLoading(true); setError(null);
    try { setData(await api.refresh(startDate, endDate, comparison)); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Refresh failed"); }
    finally { setLoading(false); }
  }

  function exportCSV() {
    if (!data) return;
    const headers = ["Campaign", "Impressions", "Clicks", "Spend ($)", "Leads", "CTR (%)", "CPL ($)", "Conv. Rate (%)"];
    const rows = (data.camp_summary ?? []).map(r => {
      const row = r as unknown as Record<string, number | string>;
      return [row.campaign, Number(row.impressions ?? 0).toFixed(0), Number(row.clicks ?? 0).toFixed(0),
        Number(row.spend ?? 0).toFixed(2), Number(row.leads ?? 0).toFixed(0),
        Number(row.ctr ?? 0).toFixed(2), Number(row.cpl ?? 0).toFixed(2),
        Number(row.conversion_rate ?? 0).toFixed(2)];
    });
    const csv = [headers, ...rows].map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "campaign_data.csv"; a.click();
    URL.revokeObjectURL(url);
  }

  const selectedClient = clients.find(c => c.id === clientId);

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Select a client and load their campaign data</p>
      </div>

      <StatusBanner />

      {/* ── Step 1: Client selector ─────────────────────────────────────────── */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold shrink-0">1</span>
          <h2 className="text-sm font-semibold text-gray-800">Select Client</h2>
          {selectedClient && (
            <span className="ml-auto text-xs text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-medium">
              ✓ {selectedClient.name}
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {clients.map(c => (
            <button key={c.id}
              onClick={() => {
                // Only clear analytics data, NOT the data source selection
                if (c.id !== clientId) {
                  setClientId(c.id);
                  setClientName(c.name);
                  setData(null as never);
                  setError(null);
                }
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                clientId === c.id
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400 hover:text-indigo-600"
              }`}>
              {c.name}
              {c.total_leads > 0 && (
                <span className={`ml-2 text-xs ${clientId === c.id ? "text-indigo-200" : "text-gray-400"}`}>
                  {c.total_leads} leads
                </span>
              )}
            </button>
          ))}

          {/* New client inline */}
          {showNewClient ? (
            <div className="flex items-center gap-2">
              <input autoFocus value={newClientName} onChange={e => setNewClientName(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") handleCreateClient(); if (e.key === "Escape") setShowNewClient(false); }}
                placeholder="Client name…"
                className="border border-indigo-400 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 w-40" />
              <button onClick={handleCreateClient} className="text-xs bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700">Add</button>
              <button onClick={() => setShowNewClient(false)} className="text-gray-400 hover:text-gray-600"><X size={14} /></button>
            </div>
          ) : (
            <button onClick={() => setShowNewClient(true)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium border border-dashed border-gray-300 text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors">
              <Plus size={14} /> New Client
            </button>
          )}
        </div>
      </div>

      {/* ── Step 2: Data source ─────────────────────────────────────────────── */}
      {clientId && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold shrink-0">2</span>
            <h2 className="text-sm font-semibold text-gray-800">Load Data</h2>
          </div>

          {/* Source toggle */}
          <div className="flex gap-3 mb-4">
            <button onClick={() => setDataSource("csv")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                dataSource === "csv" ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
              }`}>
              <Upload size={15} /> Upload CSV
            </button>
            <button onClick={() => setDataSource("platforms")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                dataSource === "platforms" ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
              }`}>
              <Globe size={15} /> Sync from Platforms
            </button>
          </div>

          {/* CSV upload */}
          {dataSource === "csv" && (
            <div className="flex flex-col sm:flex-row gap-3 items-end p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div className="flex-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">Campaign CSV</label>
                <button onClick={() => fileRef.current?.click()}
                  className="w-full border border-dashed border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors text-left">
                  {fileName ?? "📂 Choose CSV file…"}
                </button>
                <input ref={fileRef} type="file" accept=".csv" className="hidden"
                  onChange={e => { const f = e.target.files?.[0] ?? null; setFile(f); setFileName(f?.name ?? null); }} />
                <p className="text-xs text-gray-400 mt-1">
                  Need sample data?{" "}
                  <a href={api.sampleDataUrl()} download className="text-indigo-500 hover:underline">Download sample CSV</a>
                </p>
              </div>
              <button onClick={handleCSVUpload} disabled={loading || !file}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors shrink-0">
                {loading ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />}
                {loading ? "Processing…" : "Upload & Analyse"}
              </button>
            </div>
          )}

          {/* Platform sync */}
          {dataSource === "platforms" && (
            <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    🔵 Google Ads Customer ID
                    <a href="https://support.google.com/google-ads/answer/1704344" target="_blank" rel="noreferrer" className="ml-1 text-indigo-500 hover:underline text-xs">Where?</a>
                  </label>
                  <input value={googleId} onChange={e => setGoogleId(e.target.value)}
                    placeholder="e.g. 1234567890"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    🔴 Meta Ads Account ID
                    <a href="https://www.facebook.com/business/help/1492627900875762" target="_blank" rel="noreferrer" className="ml-1 text-indigo-500 hover:underline text-xs">Where?</a>
                  </label>
                  <input value={metaId} onChange={e => setMetaId(e.target.value)}
                    placeholder="e.g. act_111222333"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400" />
                </div>
              </div>

              {/* Demo quick-fill */}
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-xs text-gray-400">Demo clients:</span>
                {[
                  { name: "Ajay", g: "1234567890", m: "act_111222333" },
                  { name: "TechStartup", g: "9876543210", m: "act_444555666" },
                  { name: "EcommerceBrand", g: "1122334455", m: "act_777888999" },
                ].map(dc => (
                  <button key={dc.name} onClick={() => { setGoogleId(dc.g); setMetaId(dc.m); }}
                    className="text-xs text-indigo-600 border border-indigo-200 hover:bg-indigo-50 px-2.5 py-1 rounded-full transition-colors">
                    {dc.name}
                  </button>
                ))}
              </div>

              <button onClick={handlePlatformSync} disabled={syncing || (!googleId && !metaId)}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
                {syncing ? <Loader2 size={15} className="animate-spin" /> : <Globe size={15} />}
                {syncing ? "Syncing…" : "Sync & Analyse"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── Date filter + Refresh (only when data loaded) ───────────────────── */}
      {data && (
        <div className="flex flex-wrap gap-3 items-end bg-white border border-gray-200 rounded-xl p-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Start Date</label>
            <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">End Date</label>
            <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Compare To</label>
            <select value={comparison} onChange={e => setComparison(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
              <option>None</option>
              <option>Previous Week</option>
              <option>Previous Month</option>
            </select>
          </div>
          <button onClick={handleRefresh} disabled={loading}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-900 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />} Refresh
          </button>
          <button onClick={clearData}
            className="flex items-center gap-2 text-sm text-gray-500 border border-gray-200 hover:border-red-300 hover:text-red-500 px-4 py-2 rounded-lg transition-colors">
            <X size={14} /> Clear
          </button>
        </div>
      )}

      {data?.comparison_summary && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-sm px-4 py-3 rounded-lg">
          📊 {data.comparison_summary}
        </div>
      )}

      {/* ── Analytics output ────────────────────────────────────────────────── */}
      {data ? (
        <>
          {data.waste.total_wasted > 0 && (
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-5 py-4">
              <AlertTriangle size={18} className="text-red-500 mt-0.5 shrink-0" />
              <div className="flex-1 text-sm">
                <span className="font-semibold text-red-700">
                  ${data.waste.total_wasted.toLocaleString(undefined, { minimumFractionDigits: 2 })} in wasted spend detected
                </span>
                <span className="text-red-600"> — worst offender: <strong>{data.waste.worst_campaign}</strong>. </span>
                <span className="text-red-600">
                  Up to <strong>${data.waste.savings_opportunity.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong> is recoverable.
                </span>
              </div>
            </div>
          )}

          <KpiCards kpis={data.kpis} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <PlotlyChart data={data.charts.leads_over_time} />
            <PlotlyChart data={data.charts.spend_vs_leads} />
          </div>
          <PlotlyChart data={data.charts.campaign_performance} />

          {/* Campaign table */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-700">📋 Campaign Breakdown</h2>
              <button onClick={exportCSV}
                className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-indigo-600 border border-gray-200 hover:border-indigo-300 px-3 py-1.5 rounded-lg transition-colors">
                <Download size={12} /> Export CSV
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                  <tr>
                    {["Campaign", "Impressions", "Clicks", "Spend", "Leads", "CTR", "CPL", "Conv. Rate", "Score"].map(h => (
                      <th key={h} className="px-4 py-3 text-left font-semibold whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    const scoreMap = Object.fromEntries((data.allocation ?? []).map(a => [a.campaign, a.score]));
                    return (data.camp_summary ?? []).map((row, i) => {
                      const r = row as unknown as Record<string, number | string>;
                      const score = scoreMap[r.campaign as string];
                      return (
                        <tr key={i} className={`border-t border-gray-100 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                          <td className="px-4 py-3 font-medium text-gray-900 whitespace-nowrap">{r.campaign}</td>
                          <td className="px-4 py-3 text-gray-700">{Number(r.impressions ?? 0).toLocaleString()}</td>
                          <td className="px-4 py-3 text-gray-700">{Number(r.clicks ?? 0).toLocaleString()}</td>
                          <td className="px-4 py-3 text-gray-700">${Number(r.spend ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                          <td className="px-4 py-3 text-gray-700">{Number(r.leads ?? 0).toLocaleString()}</td>
                          <td className="px-4 py-3 text-gray-700">{Number(r.ctr ?? 0).toFixed(2)}%</td>
                          <td className="px-4 py-3 text-gray-700">${Number(r.cpl ?? 0).toFixed(2)}</td>
                          <td className="px-4 py-3 text-gray-700">{Number(r.conversion_rate ?? 0).toFixed(2)}%</td>
                          <td className="px-4 py-3">
                            {score !== undefined ? (
                              <div className="flex items-center gap-2">
                                <div className="h-1.5 rounded-full bg-indigo-400" style={{ width: `${(score / 100) * 60}px` }} />
                                <span className="font-semibold text-indigo-700">{score}</span>
                              </div>
                            ) : <span className="text-gray-400">—</span>}
                          </td>
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">💡 Diagnostic Insights</h2>
            <ul className="space-y-2">
              {data.insights.map((ins, i) => (
                <li key={i} className="text-sm text-gray-700 bg-gray-50 rounded-lg px-4 py-2">{ins}</li>
              ))}
            </ul>
          </div>
        </>
      ) : (
        !clientId ? (
          <div className="text-center py-20 text-gray-400">
            <p className="text-4xl mb-3">👆</p>
            <p className="text-sm font-medium">Select a client above to get started</p>
            <p className="text-xs mt-1">Or create a new one</p>
          </div>
        ) : !dataSource ? (
          <div className="text-center py-20 text-gray-400">
            <p className="text-4xl mb-3">📊</p>
            <p className="text-sm font-medium">Choose how to load data above</p>
            <p className="text-xs mt-1">Upload a CSV or sync from Google Ads / Meta Ads</p>
          </div>
        ) : null
      )}
    </div>
  );
}
