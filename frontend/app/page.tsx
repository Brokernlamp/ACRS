"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAppState } from "@/lib/store";
import UploadPanel from "@/components/UploadPanel";
import KpiCards from "@/components/KpiCards";
import PlotlyChart from "@/components/PlotlyChart";
import StatusBanner from "@/components/StatusBanner";
import { RefreshCw, Loader2, Download, AlertTriangle } from "lucide-react";

export default function DashboardPage() {
  const { data, setData, setLoading, loading, setError } = useAppState();
  const today = new Date().toISOString().slice(0, 10);
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
  const [startDate, setStartDate] = useState(monthAgo);
  const [endDate, setEndDate] = useState(today);
  const [comparison, setComparison] = useState("None");

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
      return [
        row.campaign,
        Number(row.impressions ?? 0).toFixed(0),
        Number(row.clicks ?? 0).toFixed(0),
        Number(row.spend ?? 0).toFixed(2),
        Number(row.leads ?? 0).toFixed(0),
        Number(row.ctr ?? 0).toFixed(2),
        Number(row.cpl ?? 0).toFixed(2),
        Number(row.conversion_rate ?? 0).toFixed(2),
      ];
    });
    const csv = [headers, ...rows].map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "campaign_data.csv"; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Upload campaign data and view performance metrics</p>
      </div>

      <StatusBanner />
      <UploadPanel />

      {/* Date filter */}
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
      </div>

      {data?.comparison_summary && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-sm px-4 py-3 rounded-lg">
          📊 {data.comparison_summary}
        </div>
      )}

      {data ? (
        <>
          {/* Wasted spend alert — prominent on dashboard */}
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

          {/* Campaign data table */}
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
                    // Merge camp_summary with allocation scores by campaign name
                    const scoreMap = Object.fromEntries(
                      (data.allocation ?? []).map(a => [a.campaign, a.score])
                    );
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

          {/* Insights */}
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
        <div className="text-center py-20 text-gray-400">
          <p className="text-4xl mb-3">📊</p>
          <p className="text-sm">Upload a CSV to activate the intelligence engine</p>
        </div>
      )}
    </div>
  );
}
