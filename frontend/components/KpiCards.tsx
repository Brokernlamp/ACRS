import { KPIs } from "@/lib/api";

const CARDS = [
  { key: "Total Spend",         icon: "💰", accent: "border-indigo-400",  sub: "Total ad spend" },
  { key: "Total Leads",         icon: "🎯", accent: "border-emerald-400", sub: "Leads generated" },
  { key: "Blended CPL (₹)",     icon: "📉", accent: "border-violet-400",  sub: "Spend ÷ leads" },
  { key: "Weighted CTR (%)",    icon: "👆", accent: "border-sky-400",     sub: "Clicks ÷ impressions" },
  { key: "Conversion Rate (%)", icon: "🔄", accent: "border-amber-400",   sub: "Leads ÷ clicks" },
  { key: "Total Clicks",        icon: "🖱️", accent: "border-slate-400",   sub: "Total clicks" },
  { key: "Total Impressions",   icon: "👁️", accent: "border-slate-400",   sub: "Total reach" },
  { key: "ROAS",                icon: "📈", accent: "border-rose-400",    sub: "Revenue ÷ spend" },
] as const;

function fmt(key: string, val: number | string): string {
  if (typeof val === "string") return val;
  if (key === "ROAS") return val === 0 ? "N/A" : `${val.toFixed(2)}x`;
  if (key.includes("₹")) return `₹${val.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
  if (key.includes("%")) return `${val.toFixed(2)}%`;
  return val.toLocaleString();
}

export default function KpiCards({ kpis }: { kpis: KPIs }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
      {CARDS.map(({ key, icon, accent, sub }) => {
        const value = kpis[key as keyof KPIs];
        return (
          <div key={key} className={`bg-white border-t-4 ${accent} rounded-xl px-3 py-3 shadow-sm`}>
            <div className="text-lg mb-0.5">{icon}</div>
            <div className="text-xl font-bold text-gray-900 tracking-tight leading-none">{fmt(key, value)}</div>
            <div className="text-xs text-gray-400 mt-1 leading-tight">{sub}</div>
          </div>
        );
      })}
    </div>
  );
}
