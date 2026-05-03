"use client";
import { useState } from "react";
import { useAppState } from "@/lib/store";
import PlotlyChart from "@/components/PlotlyChart";
import { api, SimResult } from "@/lib/api";
import { Loader2, Printer, TrendingUp, TrendingDown, Minus, Zap, AlertTriangle, DollarSign, Target } from "lucide-react";

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
  const liveCpl = cp.predicted_cpl * (1 + 0.35 * (simDelta / 100));

  const TrendIcon = lp.trend.includes("Improving") ? TrendingUp : lp.trend.includes("Declining") ? TrendingDown : Minus;
  const trendColor = lp.trend.includes("Improving") ? "text-emerald-400" : lp.trend.includes("Declining") ? "text-red-400" : "text-amber-400";

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
    } catch (e: unknown) { setSimError(e instanceof Error ? e.message : "Simulation failed"); }
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
    } catch (e: unknown) { setSimError(e instanceof Error ? e.message : "Simulation failed"); }
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

      {/* ── Dark hero header ─────────────────────────────────────────────────── */}
      <div className="bg-slate-900 rounded-2xl p-6 text-white">
        <div className="flex items-center gap-2 mb-1">
          <Zap size={18} className="text-indigo-400" />
          <h1 className="text-xl font-bold">AI Growth Engine</h1>
          {clientName && <span className="ml-auto text-xs text-slate-400 bg-slate-800 px-2 py-1 rounded-full">{clientName}</span>}
        </div>
        <p className="text-sm text-slate-400 mb-6">7-day forward intelligence based on your campaign data</p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Leads prediction */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="text-xs text-slate-400 mb-2 flex items-center gap-1.5"><Target size={12} /> Expected Leads</div>
            <div className="text-4xl font-bold text-white">{lp.predicted_leads}</div>
            <div className={`flex items-center gap-1.5 text-sm font-semibold mt-2 ${trendColor}`}>
              <TrendIcon size={14} />
              {lp.trend} · {lp.growth_rate_pct > 0 ? "+" : ""}{lp.growth_rate_pct}%
            </div>
          </div>

          {/* CPL prediction */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="text-xs text-slate-400 mb-2 flex items-center gap-1.5"><DollarSign size={12} /> Expected CPL</div>
            <div className="text-4xl font-bold text-white">₹{liveCpl.toFixed(2)}</div>
            <div className="text-xs text-slate-500 mt-2">Updates live with simulator below</div>
          </div>

          {/* CTR fatigue */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="text-xs text-slate-400 mb-2 flex items-center gap-1.5"><AlertTriangle size={12} /> CTR Fatigue</div>
            <div className="text-4xl font-bold text-white">{ctr_p.predicted_ctr}%</div>
            <div className="mt-2">
              {ctr_p.refresh_needed
                ? <span className="text-xs font-semibold text-red-400 bg-red-900/40 px-2 py-1 rounded-full">⚠ Creative refresh needed</span>
                : <span className="text-xs font-semibold text-emerald-400 bg-emerald-900/40 px-2 py-1 rounded-full">✓ Healthy — {ctr_p.drop_pct}% drop expected</span>}
            </div>
          </div>
        </div>
      </div>

      {/* ── Wasted spend alert ───────────────────────────────────────────────── */}
      {waste.total_wasted > 0 && (
        <div className="flex items-center gap-4 bg-red-950 border border-red-800 rounded-xl px-5 py-4">
          <div className="w-10 h-10 rounded-full bg-red-800 flex items-center justify-center shrink-0">
            <DollarSign size={18} className="text-red-300" />
          </div>
          <div>
            <p className="text-sm font-bold text-red-300">₹{waste.total_wasted.toLocaleString("en-IN", { minimumFractionDigits: 2 })} in inefficient spend detected</p>
            <p className="text-xs text-red-400 mt-0.5">Worst offender: <strong>{waste.worst_campaign}</strong> · Up to <strong>₹{waste.savings_opportunity.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</strong> recoverable by reallocation</p>
          </div>
        </div>
      )}

      {/* ── Recommended Actions ──────────────────────────────────────────────── */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">🎯 Recommended Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {actions.map((a, i) => {
            const isScale = a.startsWith("🚀");
            const isReview = a.startsWith("⚠️");
            const isRealloc = a.startsWith("💸");
            const bg = isScale ? "bg-emerald-50 border-emerald-200" : isReview ? "bg-amber-50 border-amber-200" : isRealloc ? "bg-indigo-50 border-indigo-200" : "bg-red-50 border-red-200";
            const badge = isScale ? "bg-emerald-100 text-emerald-700" : isReview ? "bg-amber-100 text-amber-700" : isRealloc ? "bg-indigo-100 text-indigo-700" : "bg-red-100 text-red-700";
            const label = isScale ? "SCALE" : isReview ? "REVIEW" : isRealloc ? "REALLOCATE" : "OPTIMISE";
            return (
              <div key={i} className={`border rounded-xl p-4 ${bg}`}>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${badge} mb-2 inline-block`}>{label}</span>
                <p className="text-sm text-gray-700">{a.replace(/^[^\s]+\s[^\s]+\s/, "")}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Charts ──────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PlotlyChart data={charts.leads_forecast} />
        <PlotlyChart data={charts.budget_allocation} />
      </div>

      {/* ── Performance Scores ──────────────────────────────────────────────── */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">🏆 Campaign Performance Scores</h2>
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-slate-300 text-xs uppercase">
              <tr>
                {["Campaign", "Score", "Recommended Budget", "Budget Share"].map(h => (
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
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${row.score}%` }} />
                      </div>
                      <span className="font-bold text-indigo-700 text-xs">{row.score}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-semibold text-emerald-700">
                    ₹{row.recommended_budget.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{row.budget_share_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Detected Patterns ───────────────────────────────────────────────── */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">🔍 Detected Patterns</h2>
        <div className="relative pl-5 space-y-0">
          <div className="absolute left-2 top-2 bottom-2 w-px bg-gray-200" />
          {patterns.map((p, i) => {
            const isGood = p.includes("improving") || p.includes("Best") || p.includes("spike");
            const isBad = p.includes("drop") || p.includes("Declining") || p.includes("fatigue");
            const dot = isGood ? "bg-emerald-500" : isBad ? "bg-red-500" : "bg-amber-400";
            const text = isGood ? "text-emerald-800" : isBad ? "text-red-800" : "text-amber-800";
            return (
              <div key={i} className="relative flex items-start gap-3 pb-4">
                <div className={`absolute -left-3 mt-1.5 w-2.5 h-2.5 rounded-full border-2 border-white ${dot}`} />
                <p className={`text-sm bg-white border border-gray-100 rounded-lg px-4 py-2.5 shadow-sm ${text} flex-1`}>{p}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Scenario Simulator ──────────────────────────────────────────────── */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">🧪 Scenario Simulator</h2>
          {allSimResults.length > 0 && (
            <button onClick={printSimulation} disabled={printLoading}
              className="flex items-center gap-1.5 text-xs font-semibold bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition-colors">
              {printLoading ? <Loader2 size={12} className="animate-spin" /> : <Printer size={12} />}
              {printLoading ? "Generating…" : `Print Simulation (${allSimResults.length})`}
            </button>
          )}
        </div>

        {simError && <div className="text-red-600 text-sm mb-3 bg-red-50 border border-red-200 px-4 py-2 rounded-lg">⚠️ {simError}</div>}

        <div className="bg-slate-900 rounded-2xl p-5 space-y-5">
          {/* Campaign + slider */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Campaign</label>
              <select value={simCampaign} onChange={e => setSimCampaign(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option value="">Select campaign…</option>
                {data.campaigns.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">
                Budget Change: <span className={simDelta >= 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>{simDelta > 0 ? "+" : ""}{simDelta}%</span>
                <span className="ml-3 text-slate-500">→ Est. CPL: <strong className="text-white">₹{liveCpl.toFixed(2)}</strong></span>
              </label>
              <input type="range" min={-80} max={100} step={10} value={simDelta}
                onChange={e => setSimDelta(Number(e.target.value))}
                className="w-full accent-indigo-500 mt-1" />
              <div className="flex justify-between text-xs text-slate-600 mt-1"><span>-80%</span><span>0</span><span>+100%</span></div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            <button onClick={runSim} disabled={simLoading || !simCampaign}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
              {simLoading ? <Loader2 size={14} className="animate-spin" /> : "▶"} Run Simulation
            </button>
            <button onClick={runPause} disabled={pauseLoading || !simCampaign}
              className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
              {pauseLoading ? <Loader2 size={14} className="animate-spin" /> : "⏸"} Simulate Pause
            </button>
          </div>

          {/* Results side by side */}
          {(simResult || pauseResult) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {simResult && (
                <div className={`rounded-xl p-4 border ${simResult.leads_change >= 0 ? "bg-emerald-950 border-emerald-800" : "bg-red-950 border-red-800"}`}>
                  <p className="text-xs font-bold text-slate-300 mb-3">📊 {simResult.action}</p>
                  <div className="space-y-2">
                    {[
                      { label: "Spend", val: `${simResult.spend_change >= 0 ? "+" : ""}₹${simResult.spend_change.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`, pos: simResult.spend_change >= 0 },
                      { label: "Leads", val: `${simResult.leads_change >= 0 ? "+" : ""}${simResult.leads_change}`, pos: simResult.leads_change >= 0 },
                      { label: "CPL", val: `${simResult.cpl_change >= 0 ? "+" : ""}₹${simResult.cpl_change.toFixed(2)}`, pos: simResult.cpl_change <= 0 },
                    ].map(({ label, val, pos }) => (
                      <div key={label} className="flex justify-between items-center">
                        <span className="text-xs text-slate-400">{label}</span>
                        <span className={`text-sm font-bold ${pos ? "text-emerald-400" : "text-red-400"}`}>{val}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 mt-3 italic">{simResult.summary}</p>
                </div>
              )}
              {pauseResult && (
                <div className="rounded-xl p-4 border bg-red-950 border-red-800">
                  <p className="text-xs font-bold text-slate-300 mb-3">⏸ Pause Impact</p>
                  <div className="space-y-2">
                    <div className="flex justify-between"><span className="text-xs text-slate-400">Spend Saved</span><span className="text-sm font-bold text-emerald-400">₹{Math.abs(pauseResult.spend_change).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span></div>
                    <div className="flex justify-between"><span className="text-xs text-slate-400">Leads Lost</span><span className="text-sm font-bold text-red-400">{Math.abs(pauseResult.leads_change)}</span></div>
                  </div>
                  <p className="text-xs text-slate-500 mt-3 italic">{pauseResult.summary}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* All simulations table */}
        {allSimResults.length > 0 && (
          <div className="mt-4 bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-700">All Simulations This Session</h3>
              <span className="text-xs text-gray-400">{allSimResults.length} scenario{allSimResults.length > 1 ? "s" : ""}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                  <tr>
                    {["Campaign", "Action", "Spend Δ", "Leads Δ", "CPL Δ"].map(h => (
                      <th key={h} className="px-4 py-3 text-left font-semibold whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {allSimResults.map((r, i) => (
                    <tr key={i} className={`border-t border-gray-100 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                      <td className="px-4 py-3 font-medium text-gray-900">{r.campaign}</td>
                      <td className="px-4 py-3 text-gray-600 text-xs">{r.action}</td>
                      <td className={`px-4 py-3 font-semibold text-xs ${r.spend_change >= 0 ? "text-amber-600" : "text-emerald-600"}`}>
                        {r.spend_change >= 0 ? "+" : ""}₹{r.spend_change.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                      <td className={`px-4 py-3 font-semibold text-xs ${r.leads_change >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                        {r.leads_change >= 0 ? "+" : ""}{r.leads_change}
                      </td>
                      <td className={`px-4 py-3 font-semibold text-xs ${r.cpl_change >= 0 ? "text-amber-600" : "text-emerald-600"}`}>
                        {r.cpl_change >= 0 ? "+" : ""}₹{r.cpl_change.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
