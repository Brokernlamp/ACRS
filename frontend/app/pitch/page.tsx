"use client";
import { useState } from "react";
import { Printer, Zap, TrendingUp, TrendingDown, DollarSign, Target, BarChart2, Brain, FileText, MessageSquare, CheckCircle, ArrowRight } from "lucide-react";

const DEMO = {
  client: "Your Agency Name",
  period: "Last 30 Days",
  kpis: [
    { label: "Total Spend", value: "$24,800", sub: "across 4 campaigns", color: "border-indigo-400" },
    { label: "Total Leads", value: "1,240", sub: "generated this month", color: "border-emerald-400" },
    { label: "Blended CPL", value: "$20.00", sub: "cost per lead", color: "border-violet-400" },
    { label: "ROAS", value: "4.2x", sub: "return on ad spend", color: "border-rose-400" },
  ],
  campaigns: [
    { name: "Google Search", spend: "$9,200", leads: 580, cpl: "$15.86", score: 91, trend: "up" },
    { name: "Meta Retargeting", spend: "$6,100", leads: 390, cpl: "$15.64", score: 88, trend: "up" },
    { name: "Google Display", spend: "$5,800", leads: 180, cpl: "$32.22", score: 42, trend: "down" },
    { name: "LinkedIn Awareness", spend: "$3,700", leads: 90, cpl: "$41.11", score: 31, trend: "down" },
  ],
  actions: [
    { type: "SCALE", icon: "🚀", color: "bg-emerald-50 border-emerald-200 text-emerald-800", badge: "bg-emerald-100 text-emerald-700", text: "Increase budget on Google Search by 20–30% — highest performance score (91)." },
    { type: "REALLOCATE", icon: "💸", color: "bg-indigo-50 border-indigo-200 text-indigo-800", badge: "bg-indigo-100 text-indigo-700", text: "$4,200 in inefficient spend detected. Shift budget from Google Display → Google Search." },
    { type: "REVIEW", icon: "⚠️", color: "bg-amber-50 border-amber-200 text-amber-800", badge: "bg-amber-100 text-amber-700", text: "LinkedIn Awareness has the lowest score (31) — audit creatives and targeting." },
    { type: "OPTIMISE", icon: "✂️", color: "bg-red-50 border-red-200 text-red-800", badge: "bg-red-100 text-red-700", text: "Google Display CPL $32.22 is 61% above average — reduce bids or tighten audience." },
  ],
  simulation: {
    campaign: "Google Search",
    delta: "+20%",
    spendChange: "+$1,840",
    leadsChange: "+98",
    cplChange: "+$1.11",
    summary: "Increasing Google Search budget by 20% is projected to generate 98 additional leads at a marginal CPL of $18.78 — still well below your target.",
  },
  predictions: { leads: 310, trend: "📈 Improving", growth: "+8.4%", cpl: "$19.20", ctr: "2.4%" },
  waste: { total: "$4,200", recoverable: "$2,520", worst: "Google Display" },
  features: [
    { icon: BarChart2, title: "Live Dashboard", desc: "Real-time KPIs, campaign breakdown, wasted spend alerts — all in one view." },
    { icon: Brain, title: "AI Growth Engine", desc: "7-day predictions, performance scores, budget reallocation recommendations." },
    { icon: Target, title: "Scenario Simulator", desc: "Test budget changes before making them. See projected leads and CPL impact instantly." },
    { icon: FileText, title: "Automated Reports", desc: "One-click PDF reports. Standard or full AI Growth Strategy — emailed directly to clients." },
    { icon: MessageSquare, title: "AI Chatbot", desc: "Ask anything about your campaigns. Get data-backed answers in plain English." },
    { icon: DollarSign, title: "Multi-Platform", desc: "Google Ads + Meta Ads merged into one view. Blended CPL, cross-platform P&L." },
  ],
};

export default function PitchPage() {
  const [clientName, setClientName] = useState(DEMO.client);
  const [editing, setEditing] = useState(false);

  return (
    <div className="min-h-screen bg-white print:bg-white">
      {/* Print / Edit toolbar — hidden when printing */}
      <div className="print:hidden sticky top-0 z-50 bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Zap size={14} className="text-white" />
          </div>
          <span className="font-bold text-gray-900 text-sm">AI Growth Operator — Pitch Deck</span>
        </div>
        <div className="flex items-center gap-3">
          {editing ? (
            <div className="flex items-center gap-2">
              <input
                autoFocus
                value={clientName}
                onChange={e => setClientName(e.target.value)}
                onBlur={() => setEditing(false)}
                onKeyDown={e => e.key === "Enter" && setEditing(false)}
                className="border border-indigo-400 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 w-48"
              />
            </div>
          ) : (
            <button onClick={() => setEditing(true)}
              className="text-xs text-gray-500 border border-gray-200 hover:border-indigo-300 hover:text-indigo-600 px-3 py-1.5 rounded-lg transition-colors">
              ✏️ Edit client name
            </button>
          )}
          <button onClick={() => window.print()}
            className="flex items-center gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-1.5 rounded-lg transition-colors">
            <Printer size={13} /> Print / Save PDF
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-10 space-y-12 print:py-6 print:space-y-8">

        {/* ── Cover ─────────────────────────────────────────────────────────── */}
        <div className="bg-slate-900 rounded-2xl p-10 text-white print:rounded-none">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <span className="font-bold text-lg">AI Growth Operator</span>
          </div>
          <h1 className="text-4xl font-bold leading-tight mb-3">
            Stop guessing.<br />
            <span className="text-indigo-400">Start growing.</span>
          </h1>
          <p className="text-slate-400 text-lg max-w-xl">
            AI-powered marketing analytics that tells you exactly where your budget is being wasted, which campaigns to scale, and what to do next.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <span className="text-sm text-slate-400">Prepared for</span>
            <span className="text-white font-bold text-lg border-b border-indigo-400 pb-0.5">{clientName}</span>
          </div>
        </div>

        {/* ── The Problem ───────────────────────────────────────────────────── */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">The problem with most ad reporting</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { icon: "📊", title: "Data without direction", desc: "You get numbers but no clear answer on what to do with them. Impressions, clicks, CTR — but no action." },
              { icon: "💸", title: "Budget leaking silently", desc: "On average, 17–30% of ad spend goes to underperforming campaigns. Most agencies never catch it." },
              { icon: "⏱️", title: "Hours on manual reports", desc: "Building client reports takes 3–5 hours per client per month. That's time you could spend on strategy." },
            ].map(({ icon, title, desc }) => (
              <div key={title} className="border border-gray-200 rounded-xl p-5">
                <div className="text-3xl mb-3">{icon}</div>
                <h3 className="font-bold text-gray-900 mb-2">{title}</h3>
                <p className="text-sm text-gray-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Live Demo: KPIs ───────────────────────────────────────────────── */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full uppercase tracking-wide">Live Demo</span>
            <h2 className="text-xl font-bold text-gray-900">Dashboard — {DEMO.period}</h2>
          </div>
          <p className="text-sm text-gray-500 mb-5">This is what your dashboard looks like the moment data is loaded.</p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            {DEMO.kpis.map(k => (
              <div key={k.label} className={`bg-white border-t-4 ${k.color} border border-gray-100 rounded-xl px-4 py-4 shadow-sm`}>
                <div className="text-2xl font-bold text-gray-900">{k.value}</div>
                <div className="text-xs font-semibold text-gray-700 mt-1">{k.label}</div>
                <div className="text-xs text-gray-400 mt-0.5">{k.sub}</div>
              </div>
            ))}
          </div>

          {/* Wasted spend callout */}
          <div className="flex items-center gap-4 bg-red-50 border border-red-200 rounded-xl px-5 py-4 mb-6">
            <div className="text-2xl">🚨</div>
            <div>
              <p className="text-sm font-bold text-red-700">{DEMO.waste.total} in wasted spend detected automatically</p>
              <p className="text-xs text-red-500 mt-0.5">Worst offender: <strong>{DEMO.waste.worst}</strong> · Up to <strong>{DEMO.waste.recoverable}</strong> is recoverable by reallocation</p>
            </div>
          </div>

          {/* Campaign table */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
              <h3 className="text-sm font-semibold text-gray-700">📋 Campaign Breakdown</h3>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-slate-900 text-slate-300 text-xs uppercase">
                <tr>
                  {["Campaign", "Spend", "Leads", "CPL", "AI Score", "Trend"].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {DEMO.campaigns.map((c, i) => (
                  <tr key={i} className={`border-t border-gray-100 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                    <td className="px-4 py-3 font-medium text-gray-900">{c.name}</td>
                    <td className="px-4 py-3 text-gray-700">{c.spend}</td>
                    <td className="px-4 py-3 text-gray-700">{c.leads}</td>
                    <td className="px-4 py-3 text-gray-700">{c.cpl}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-1.5">
                          <div className={`h-1.5 rounded-full ${c.score >= 70 ? "bg-emerald-500" : c.score >= 50 ? "bg-amber-400" : "bg-red-500"}`} style={{ width: `${c.score}%` }} />
                        </div>
                        <span className={`text-xs font-bold ${c.score >= 70 ? "text-emerald-700" : c.score >= 50 ? "text-amber-700" : "text-red-700"}`}>{c.score}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {c.trend === "up"
                        ? <span className="flex items-center gap-1 text-xs text-emerald-600"><TrendingUp size={12} /> Growing</span>
                        : <span className="flex items-center gap-1 text-xs text-red-500"><TrendingDown size={12} /> Declining</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── AI Recommendations ────────────────────────────────────────────── */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full uppercase tracking-wide">AI Engine</span>
            <h2 className="text-xl font-bold text-gray-900">What the AI recommends</h2>
          </div>
          <p className="text-sm text-gray-500 mb-5">Generated automatically from your data. No manual analysis needed.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {DEMO.actions.map((a, i) => (
              <div key={i} className={`border rounded-xl p-4 ${a.color}`}>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${a.badge} mb-2 inline-block`}>{a.type}</span>
                <p className="text-sm">{a.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Scenario Simulator ────────────────────────────────────────────── */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full uppercase tracking-wide">Simulator</span>
            <h2 className="text-xl font-bold text-gray-900">Test budget changes before making them</h2>
          </div>
          <p className="text-sm text-gray-500 mb-5">Show clients exactly what happens if you increase or decrease budget on any campaign.</p>

          <div className="bg-slate-900 rounded-2xl p-6 text-white">
            <p className="text-sm text-slate-400 mb-4">Scenario: Increase <strong className="text-white">{DEMO.simulation.campaign}</strong> budget by <strong className="text-indigo-400">{DEMO.simulation.delta}</strong></p>
            <div className="grid grid-cols-3 gap-4 mb-4">
              {[
                { label: "Additional Spend", value: DEMO.simulation.spendChange, pos: false },
                { label: "Additional Leads", value: DEMO.simulation.leadsChange, pos: true },
                { label: "CPL Change", value: DEMO.simulation.cplChange, pos: false },
              ].map(({ label, value, pos }) => (
                <div key={label} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <div className="text-xs text-slate-400 mb-1">{label}</div>
                  <div className={`text-2xl font-bold ${pos ? "text-emerald-400" : "text-amber-400"}`}>{value}</div>
                </div>
              ))}
            </div>
            <p className="text-sm text-slate-400 italic">{DEMO.simulation.summary}</p>
          </div>
        </div>

        {/* ── 7-day predictions ─────────────────────────────────────────────── */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full uppercase tracking-wide">Predictions</span>
            <h2 className="text-xl font-bold text-gray-900">7-day forward forecast</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Expected Leads", value: DEMO.predictions.leads, sub: "next 7 days" },
              { label: "Trend", value: DEMO.predictions.trend, sub: DEMO.predictions.growth },
              { label: "Expected CPL", value: DEMO.predictions.cpl, sub: "projected" },
              { label: "Expected CTR", value: DEMO.predictions.ctr, sub: "after fatigue decay" },
            ].map(({ label, value, sub }) => (
              <div key={label} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                <div className="text-xs text-gray-400 mb-1">{label}</div>
                <div className="text-xl font-bold text-gray-900">{value}</div>
                <div className="text-xs text-gray-400 mt-1">{sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Features ──────────────────────────────────────────────────────── */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Everything included</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {DEMO.features.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="border border-gray-200 rounded-xl p-5 hover:border-indigo-300 transition-colors">
                <div className="w-9 h-9 bg-indigo-50 rounded-lg flex items-center justify-center mb-3">
                  <Icon size={18} className="text-indigo-600" />
                </div>
                <h3 className="font-bold text-gray-900 mb-1">{title}</h3>
                <p className="text-sm text-gray-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── What you get ──────────────────────────────────────────────────── */}
        <div className="bg-indigo-600 rounded-2xl p-8 text-white print:rounded-none">
          <h2 className="text-2xl font-bold mb-6">What you get from day one</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              "Instant visibility into wasted ad spend",
              "AI-generated recommendations every time data loads",
              "7-day lead and CPL forecasts",
              "Budget scenario simulator before any change",
              "One-click PDF reports for client meetings",
              "AI chatbot that answers questions about your data",
              "Google Ads + Meta Ads merged into one view",
              "Automated email reports to clients",
            ].map(item => (
              <div key={item} className="flex items-start gap-2.5">
                <CheckCircle size={16} className="text-indigo-300 mt-0.5 shrink-0" />
                <span className="text-sm text-indigo-100">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Next steps ────────────────────────────────────────────────────── */}
        <div className="border border-gray-200 rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Ready to get started?</h2>
          <p className="text-gray-500 mb-6">Setup takes under 10 minutes. Upload a CSV export from your ad platform and the AI does the rest.</p>
          <div className="space-y-3">
            {[
              { step: "1", text: "Create a client profile with your target CPL and monthly budget" },
              { step: "2", text: "Upload a CSV export from Google Ads or Meta Ads (or connect directly)" },
              { step: "3", text: "Get instant AI analysis, recommendations, and a printable report" },
            ].map(({ step, text }) => (
              <div key={step} className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-full bg-indigo-600 text-white text-sm font-bold flex items-center justify-center shrink-0">{step}</div>
                <p className="text-sm text-gray-700">{text}</p>
                <ArrowRight size={14} className="text-gray-300 ml-auto shrink-0" />
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-400 pb-4">
          AI Growth Operator · Prepared for {clientName} · {new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" })}
        </div>
      </div>
    </div>
  );
}
