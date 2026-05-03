"use client";
import { useState } from "react";
import { useAppState } from "@/lib/store";
import PlotlyChart from "@/components/PlotlyChart";
import { api, SimResult } from "@/lib/api";
import { Loader2, Printer } from "lucide-react";

export default function AiEnginePage() {
  const { data, clientName } = useAppState();
  const [simCampaign, setSimCampaign] = useState("");
  const [simDelta, setSimDelta] = useState(20);
  const [simResult, setSimResult] = useState<SimResult | null>(null);
  const [pauseResult, setPauseResult] = useState<SimResult | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [pauseLoading, setPauseLoading] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);
  const [printLoading, setPrintLoading] = useState(false);
  const [allSimResults, setAllSimResults] = useState<SimResult[]>([]);

  if (!data) {
    return (
      <div className="text-center py-20 text-gray-400">
        <p className="text-4xl mb-3">🧠</p>
        <p className="text-sm">Upload data on the Dashboard first</p>
      </div>
    );
  }

  const { predictions: lp, cpl_prediction: cp, ctr_prediction: ctr_p, actions, waste, allocation, patterns, charts } = data;
  const trendColor = lp.trend.includes("Improving") ? "text-emerald-600" : lp.trend.includes("Declining") ? "text-red-500" : "text-amber-500";

  // Live CPL estimate based on simulator delta
  const liveCpl = cp.predicted_cpl * (1 + 0.35 * (simDelta / 100));

  async function runSim() {
    if (!simCampaign) return;
    setSimLoading(true); setSimError(null);
    try {
      const result = await api.simulate(simCampaign, simDelta);
      setSimResult(result);
      setAllSimResults(prev => {
        const filtered = prev.filter(r => !(r.campaign === result.campaign && r.action === result.action));
        return [...filtered, result];
      });
    }
    catch (e: unknown) { setSimError(e instanceof Error ? e.message : "Simulation failed"); }
    finally { setSimLoading(false); }
  }

  async function runPause() {
    if (!simCampaign) return;
    setPauseLoading(true); setSimError(null);
    try {
      const result = await api.simulatePause(simCampaign);
      setPauseResult(result);
      setAllSimResults(prev => {
        const filtered = prev.filter(r => !(r.campaign === result.campaign && r.action === "Pause"));
        return [...filtered, result];
      });
    }
    catch (e: unknown) { setSimError(e instanceof Error ? e.message : "Simulation failed"); }
    finally { setPauseLoading(false); }
  }

  async function printSimulation() {
    if (!allSimResults.length) return;
    setPrintLoading(true);
    try {
      const blob = await api.reportSimulation(clientName || "Client", allSimResults);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${clientName || "client"}_simulation_report.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      setSimError(e instanceof Error ? e.message : "Print failed");
    } finally { setPrintLoading(false); }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Growth Engine</h1>
        <p className="text-sm text-gray-500 mt-1">Predictions, recommendations, and scenario simulations</p>
      </div>

      {/* Predictions */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">📈 Predictions — Next 7 Days</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="text-xs text-gray-500 mb-1">🎯 Expected Leads</div>
            <div className="text-3xl font-bold text-gray-900">{lp.predicted_leads}</div>
            <div className={`text-sm font-semibold mt-1 ${trendColor}`}>{lp.trend} · {lp.growth_rate_pct > 0 ? "+" : ""}{lp.growth_rate_pct}%</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="text-xs text-gray-500 mb-1">💸 Expected CPL</div>
            <div className="text-3xl font-bold text-gray-900">${liveCpl.toFixed(2)}</div>
            <div className="text-xs text-gray-400 mt-1">Updates live with simulator ↓</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="text-xs text-gray-500 mb-1">👁️ Expected CTR</div>
            <div className="text-3xl font-bold text-gray-900">{ctr_p.predicted_ctr}%</div>
            <div className="text-sm mt-1">
              Fatigue drop: {ctr_p.drop_pct}% &nbsp;
              {ctr_p.refresh_needed
                ? <span className="text-red-500 font-semibold">⚠️ Refresh Needed</span>
                : <span className="text-emerald-600 font-semibold">✅ Healthy</span>}
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PlotlyChart data={charts.leads_forecast} />
        <PlotlyChart data={charts.campaign_performance} />
      </div>

      {/* Recommended Actions */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">🎯 Recommended Actions</h2>
        <div className="space-y-2">
          {actions.map((a, i) => {
            const color = a.startsWith("🚀") ? "border-emerald-400 bg-emerald-50"
              : a.startsWith("⚠️") ? "border-amber-400 bg-amber-50"
              : a.startsWith("💸") ? "border-indigo-400 bg-indigo-50"
              : "border-red-400 bg-red-50";
            return <div key={i} className={`border-l-4 px-4 py-3 rounded-r-lg text-sm ${color}`}>{a}</div>;
          })}
        </div>
      </section>

      {/* Performance Scores with sub-scores */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">🏆 Campaign Performance Scores</h2>
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-indigo-600 text-white">
              <tr>
                {["Campaign", "Overall Score", "CTR", "CPL ($)", "Conv. Rate (%)", "Recommended Budget"].map(h => (
                  <th key={h} className="px-4 py-3 text-left font-semibold whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allocation.map((row, i) => (
                <tr key={i} className={`border-t border-gray-100 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                  <td className="px-4 py-3 font-medium text-gray-900">{row.campaign}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[80px]">
                        <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${row.score}%` }} />
                      </div>
                      <span className="font-bold text-indigo-700">{row.score}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">—</td>
                  <td className="px-4 py-3 text-gray-600">—</td>
                  <td className="px-4 py-3 text-gray-600">—</td>
                  <td className="px-4 py-3 font-semibold text-emerald-700">
                    ${row.recommended_budget.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    <span className="text-xs text-gray-400 ml-1">({row.budget_share_pct}%)</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Budget comparison chart */}
      <PlotlyChart data={charts.budget_allocation} />

      {/* Detected Patterns */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">🔍 Detected Patterns</h2>
        <div className="space-y-2">
          {patterns.map((p, i) => {
            const cls = p.includes("improving") || p.includes("Best") || p.includes("spike")
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : p.includes("drop") || p.includes("Declining")
              ? "bg-red-50 border-red-200 text-red-800"
              : "bg-amber-50 border-amber-200 text-amber-800";
            return <div key={i} className={`border rounded-lg px-4 py-3 text-sm ${cls}`}>{p}</div>;
          })}
        </div>
      </section>

      {/* Scenario Simulator */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">🧪 Scenario Simulator</h2>
          {allSimResults.length > 0 && (
            <button
              onClick={printSimulation}
              disabled={printLoading}
              className="flex items-center gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition-colors">
              {printLoading ? <Loader2 size={12} className="animate-spin" /> : <Printer size={12} />}
              {printLoading ? "Generating…" : `Print Simulation (${allSimResults.length})`}
            </button>
          )}
        </div>
        {simError && <div className="text-red-600 text-sm mb-3">⚠️ {simError}</div>}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-gray-700">Budget Change Simulation</h3>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Campaign</label>
              <select value={simCampaign} onChange={e => setSimCampaign(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
                <option value="">Select campaign…</option>
                {data.campaigns.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Budget Change: <span className={simDelta >= 0 ? "text-emerald-600 font-semibold" : "text-red-500 font-semibold"}>{simDelta > 0 ? "+" : ""}{simDelta}%</span>
                <span className="ml-3 text-gray-400">→ Est. CPL: <strong className="text-gray-700">${liveCpl.toFixed(2)}</strong></span>
              </label>
              <input type="range" min={-80} max={100} step={10} value={simDelta}
                onChange={e => setSimDelta(Number(e.target.value))}
                className="w-full accent-indigo-600" />
              <div className="flex justify-between text-xs text-gray-400 mt-1"><span>-80%</span><span>0</span><span>+100%</span></div>
            </div>
            <button onClick={runSim} disabled={simLoading || !simCampaign}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
              {simLoading ? <Loader2 size={14} className="animate-spin" /> : "▶"} Run Simulation
            </button>
            {simResult && (
              <div className={`rounded-lg p-4 text-sm border ${simResult.leads_change >= 0 ? "bg-emerald-50 border-emerald-200" : "bg-red-50 border-red-200"}`}>
                <p className="font-semibold mb-2">📊 {simResult.action} — {simResult.campaign}</p>
                <p>💰 Spend: <strong>{simResult.spend_change >= 0 ? "+" : ""}${simResult.spend_change.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></p>
                <p>🎯 Leads: <strong>{simResult.leads_change >= 0 ? "+" : ""}{simResult.leads_change}</strong></p>
                <p>📉 CPL: <strong>{simResult.cpl_change >= 0 ? "+" : ""}${simResult.cpl_change.toFixed(2)}</strong></p>
                <p className="mt-2 italic text-gray-600">{simResult.summary}</p>
              </div>
            )}
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-gray-700">Pause Simulation</h3>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Campaign to Pause</label>
              <select value={simCampaign} onChange={e => setSimCampaign(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
                <option value="">Select campaign…</option>
                {data.campaigns.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <button onClick={runPause} disabled={pauseLoading || !simCampaign}
              className="flex items-center gap-2 bg-gray-700 hover:bg-gray-800 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
              {pauseLoading ? <Loader2 size={14} className="animate-spin" /> : "⏸"} Simulate Pause
            </button>
            {pauseResult && (
              <div className="rounded-lg p-4 text-sm border bg-red-50 border-red-200">
                <p className="font-semibold mb-2">⏸️ Pause — {pauseResult.campaign}</p>
                <p>💰 Spend Saved: <strong>${Math.abs(pauseResult.spend_change).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></p>
                <p>🎯 Leads Lost: <strong>{Math.abs(pauseResult.leads_change)}</strong></p>
                <p className="mt-2 italic text-gray-600">{pauseResult.summary}</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
